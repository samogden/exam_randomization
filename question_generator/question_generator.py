#!env python
import datetime
import random
import sys
import time
from typing import List

import textwrap

import inspect
import importlib


import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

class Variable:
  def __init__(self, name, true_value):
    self.name = name
    self.true_value = true_value
    self.given_value = None
    self.id = id(self)
  def answer_question(self, given_value):
    self.given_value = given_value
  def compare(self):
    self.result = str(self.given_value) == str(self.true_value)
    return self.result
  def get_feedback(self):
    if self.compare():
      return f"Correct! {self.true_value} == {self.given_value}"
    else:
      return f"Incorrect! {self.true_value} != {self.given_value} (your answer)"
  
  def __str__(self):
    return f"{self.name}: {self.true_value}"
  
  def get_info(self):
    return (self.name, self.id, self.true_value)

  def get_markdown_answers(self) -> List[str]:
    return [f"* {self.true_value}\n"]

class VariableFloat(Variable):
  precision = 3
  def __init__(self, name, true_value, epsilon=0.1):
    self.epsilon = epsilon
    super().__init__(name, true_value)
  def answer_question(self, given_value):
    try:
      self.given_value = float(given_value)
    except ValueError:
      logging.error("Cannot interpret input as float")
      self.given_value = float("nan")
  def compare(self):
    self.result = (self.true_value - self.epsilon <= self.given_value) and (self.given_value <= self.true_value + self.epsilon)
    return self.result
  def get_feedback(self):
    if self.compare():
      return f"Correct! {self.true_value: 0.3f} == {self.given_value: 0.3f}"
    else:
      return f"Incorrect! {self.true_value: 0.3f} != {self.given_value: 0.3f} (your answer)"
  
  def get_markdown_answers(self, precision=None) -> List[str]:
    if precision is None:
      precision = self.precision
    return [f"= {self.true_value:.{precision}f} +- {self.epsilon}\n"]

class VariableHex(Variable):
  def __init__(self, *args, num_bits=0, **kwargs):
    super().__init__(*args, **kwargs)
    self.num_bits = num_bits
  def get_markdown_answers(self) -> List[str]:
    return [
      f"* {self.true_value}",
      f"* {self.true_value:x}",
      f"* 0x{self.true_value:X}",
      f"* {self.true_value:0{self.num_bits}b}",
      f"* 0b{self.true_value:0{self.num_bits}b}"
    ]

def escape_markdown(l) -> str:
  return l.replace('#', '\#')

class Question:
  
  # todo: create question from given information, so we can recreate as necessary.  Basically pickle it lol
  def __init__(self, given_vars: List[Variable], target_vars: List[Variable] = None, *args, **kwargs):
    self.given_vars = given_vars
    if target_vars is None:
      target_vars = random.choices(self.given_vars, k=1)
      self.given_vars.remove(target_vars[0])
    self.target_vars = target_vars
  
  def get_tuple(self):
    return tuple([var.true_value for var in sorted(self.target_vars + self.given_vars, key=(lambda v: v.name))])
  
  def __eq__(self, other):
    return self.get_tuple() == other.get_tuple()
  
  def check(self):
    for variable in self.target_vars:
      logging.info(variable.get_feedback())
  
  def get_question_prelude(self) -> List[str]:
    return ["Given the below information, please answer the questions."]
  
  def get_question_body(self) -> List[str]:
    return [f"{var.name} : {var.true_value}\n" for var in self.given_vars]
    
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

  def get_explanation(self) -> List[str]:
    return [] # todo

  def to_markdown(self) -> str:
    # markdown_text = f"Title: {self.__class__.__name__}\n"
    # markdown_text += f"Points: 4\n"
    
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
  def generate_group_markdown(cls, num_variations = 1000, max_tries=100000, points_per_question=4, num_to_pick=1):
    questions = set()
    markdown_text = "GROUP\n"
    markdown_text += f"pick: {num_to_pick}\n"
    markdown_text += f"points per question: {points_per_question}\n"
    markdown_text += "\n"
    num_tries = 0
    while (len(questions) < num_variations) and num_tries < max_tries:
      num_tries += 1
      q_text = cls().to_markdown()
      if q_text in questions:
        continue
      questions.add(q_text)
      markdown_text += f"{1}." + q_text
      markdown_text += "\n\n"
    markdown_text += "END_GROUP"
    return markdown_text


def main():

  modules = [
    "math_questions",
    "memory_questions",
    # "process_questions"
  ]

  def get_classes(module):
    return [obj for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and obj.__module__ == module.__name__]
    
  
  with open("files/temp.md", 'w') as fid:
    fid.write(
      textwrap.dedent(
        f"""
        Quiz title: {datetime.datetime.now()}
        Quiz description: trying out some new generation things
        
        """
      )
    )
    
    for module in modules:
      m = importlib.import_module(module)
      for c in get_classes(m):
        if "MemoryAccessQuestion" in c.__name__: continue # todo: fix this hack
        logging.debug(c)
        fid.write(c.generate_group_markdown(num_variations=100, points_per_question=2))
        fid.write("\n\n")

if __name__ == "__main__":
  main()
