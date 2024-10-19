#!env python
import logging
import sys
import textwrap
import time
import random
from typing import List, Dict

from .variable import Variable

class Question:
  
  # todo: create question from given information, so we can recreate as necessary.  Basically pickle it lol
  def __init__(self, given_vars: List[Variable]=None, target_vars: List[Variable] = None, *args, **kwargs):
    self.given_vars = given_vars
    if self.given_vars is not None:
      if target_vars is None:
        target_vars = random.choices(self.given_vars, k=1)
        self.given_vars.remove(target_vars[0])
    self.target_vars = target_vars
    self.img = None
  
  def get_tuple(self):
    return tuple([var.true_value for var in sorted(self.target_vars + self.given_vars, key=(lambda v: v.name))])
  
  def __eq__(self, other):
    return self.get_tuple() == other.get_tuple()
  
  def check(self):
    for variable in self.target_vars:
      logging.info(variable.get_feedback())
  
  def get_question_prelude(self, *args, **kwargs) -> List[str]:
    return ["Given the below information, please answer the questions."]
  
  def get_question_body(self, *args, **kwargs) -> List[str]:
    return [f"{var}\n" for var in self.given_vars]
  
  def print_question(self) -> None:
    print(''.join(self.get_question_prelude()))
    print(''.join(self.get_question_body()))
  
  def ask_question(self):
    self.print_question()
    for var in self.target_vars:
      var.answer_question(input(f"{var.name}: ").strip())
    
    time.sleep(0.1)
    self.check()
    sys.stderr.flush()
    sys.stdout.flush()
    time.sleep(0.1)
  
  def get_explanation(self, *args, **kwargs) -> List[str]:
    return [] # todo
  
  def to_markdown(self) -> str:

    def escape_markdown(l) -> str:
      return l.replace('#', '\#')
  
  
    question_body = ""
    question_body += '\n'.join(self.get_question_prelude()) + "\n\n"
    question_body += '\n\n'.join(map(escape_markdown, self.get_question_body())) + "\n\n"
    
    target_var = random.choice(self.target_vars)
    question_body += f"{escape_markdown(target_var.name)} : ??\n"
    
    explanation_lines = self.get_explanation()
    if len(explanation_lines) > 0:
      explanation_block = '\n\n'.join(self.get_explanation()) + '\n'
    else:
      explanation_block = ""
    
    answer_block = '\n'.join(sorted(set(target_var.get_markdown_answers())))
    
    
    
    markdown_text = (
        textwrap.indent(question_body, '\t')
        + ("..." if (len(explanation_lines) > 0) else "") + textwrap.indent(explanation_block, '\t')
        + textwrap.indent(answer_block, '')
    )
    
    return markdown_text
  
  @classmethod
  def generate_question_set(cls, num_variations, max_tries=None, module_kwargs={}):
    if max_tries is None: max_tries=100*num_variations
    questions = set()
    num_tries = 0
    while (len(questions) < num_variations) and num_tries < max_tries:
      num_tries += 1
      q_text = cls(**module_kwargs).to_markdown()
      if q_text in questions:
        continue
      questions.add(q_text)
    return questions
  
  @classmethod
  def generate_group_markdown(cls, num_variations, max_tries=None, points_per_question=4, num_to_pick=1, module_kwargs={}):
    
    markdown_text = "GROUP\n"
    markdown_text += f"pick: {num_to_pick}\n"
    markdown_text += f"points per question: {points_per_question}\n"
    markdown_text += "\n"
    questions = cls.generate_question_set(num_variations, max_tries, module_kwargs=module_kwargs)
    for q_text in questions:
      markdown_text += f"{1}." + q_text
      markdown_text += "\n\n"
    markdown_text += "END_GROUP"
    return markdown_text
  
  @classmethod
  def get_table_lines_markdown(cls,
      table_data: Dict[str,List[str]],
      headers: List[str],
      sorted_keys: List[str] = None,
      add_header_space: bool = False
  ) -> List[str]:
    
    if add_header_space:
      table_lines = '| ' + '| '.join([" "] + headers) + "|\n"
      table_lines += "|:-" + "|-:" * (len(headers)) + "|\n"
    else:
      table_lines = '| ' + '| '.join(headers) + "|\n"
      table_lines += "|:-" * (len(headers)) + "|\n"
    
    # table_lines += "|:---- | :----|\n"
    if sorted_keys is None:
      sorted_keys = sorted(table_data.keys())
    for key in sorted_keys:
      table_lines += '| ' + ' | '.join([f"**{key}**"] + [str(d) for d in table_data[key]]) + ' |\n'
    
    return [table_lines]
  
  @classmethod
  def get_table_lines_html(cls,
      table_data: Dict[str,List[str]],
      headers: List[str] = [],
      sorted_keys: List[str] = None,
      add_header_space: bool = False,
      hide_keys: bool = False
  ) -> List[str]:
    
    table_lines = ["<table  style=\"border: 1px solid black;\">"]
    table_lines.append("<tr>")
    if add_header_space:
      table_lines.append("<th></th>")
    table_lines.extend([
      f"<th style=\"padding: 5px;\">{h}</th>"
      for h in headers
    ])
    table_lines.append("</tr>")
    
    if sorted_keys is None:
      sorted_keys = sorted(table_data.keys())
    
    for key in sorted_keys:
      table_lines.append("<tr>")
      if not hide_keys:
        table_lines.append(
          f"<td style=\"border: 1px solid black; white-space:pre; padding: 5px;\"><b>{key}</b></td>"
        )
      table_lines.extend([
        f"<td style=\"border: 1px solid black; white-space:pre; padding: 5px;\">{cell_text}</td>"
        for cell_text in table_data[key]
      ])
      table_lines.append("</tr>")
    
    table_lines.append("</table>")
      
    return ['\n'.join(table_lines)]
  
  @classmethod
  def get_table_lines(cls, *args, output_markdown=False, **kwargs):
    if output_markdown:
      return cls.get_table_lines_markdown(*args, **kwargs)
    else:
      return cls.get_table_lines_html(*args, **kwargs)
    
class CanvasQuestion(Question):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.blank_vars: Dict[str,Variable] = {}
  
  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return all([self.blank_vars[key] == other.blank_vars[key] for key in self.blank_vars.keys()])
    return False
  
  def __hash__(self):
    logging.debug(f'hash: {[f"{self.blank_vars[key]}" for key in sorted(self.blank_vars.keys())]}')
    return hash(''.join([f"{self.blank_vars[key]}" for key in sorted(self.blank_vars.keys())]) + ''.join(self.get_question_body()))