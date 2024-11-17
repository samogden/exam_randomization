#!env python

from __future__ import annotations


import abc
import datetime
import enum
import inspect
import pprint

import canvasapi.course
import canvasapi.quiz
import pypandoc
import yaml
from typing import List, Dict, Any, Tuple
import jinja2

import logging

from misc import OutputFormat
import markdown

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


from exam_generation_functions import QuickFunctions


class Answer():
  class AnswerKind(enum.Enum):
    BLANK = "fill_in_multiple_blanks_question"
    MULTIPLE_CHOICE = enum.auto() # todo: have baffles?
  class VariableKind(enum.Enum): # todo: use these for generate variations?
    INT = enum.auto()
    FLOAT = enum.auto()
  def __init__(self, key:str, value, kind : Answer.AnswerKind, display=None):
    self.key = key
    self.value = value
    self.kind = kind
    self.display = display if display is not None else value
  
  def get_for_canvas(self):
    canvas_answer = {
      "blank_id": self.key,
      "answer_text": self.value,
      "answer_weight": 100,
    }
    return canvas_answer

class Question(abc.ABC):
  """
  A question base class that will be able to output questions to a variety of formats.
  """
  
  # todo: when calculating hash, have an attribute "max repeats" that will return the hash with a field that will stop changing after a certain number of repeats
  
  class TOPIC(enum.Enum):
    PROCESS = enum.auto()
    MEMORY = enum.auto()
    THREADS = enum.auto()
    IO = enum.auto()
    PROGRAMMING = enum.auto()
    MISC = enum.auto()
    
    @classmethod
    def from_string(cls, string) -> Question.TOPIC:
      mapping = {
        "processes": cls.PROCESS,
        "memory": cls.MEMORY,
        "threads": cls.THREADS,
        "io": cls.IO,
        "programing" : cls.PROGRAMMING,
        "misc": cls.MISC,
      }
      if string.lower() in mapping:
        return mapping.get(string.lower())
      return cls.MISC
  
  # todo: Add in an enum for kind of answer, or a separate class that can handle formatting for us for ease.
  
  
  def __init__(self, name: str, value: float, kind: Question.TOPIC, *args, **kwargs):
    self.name = name
    self.value = value
    self.kind = kind
    
    self.extra_attrs = kwargs # clear page, etc.
    
    # todo: use these
    # self.given_vars = {}
    # self.target_vars = {}
    # self.intermediate_vars = {}
  
  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return all([self.blank_vars[key] == other.blank_vars[key] for key in self.blank_vars.keys()])
    return False
  
  def __hash__(self):
    logging.debug(f'hash: {[f"{self.blank_vars[key]}" for key in sorted(self.blank_vars.keys())]}')
    return hash(''.join([f"{self.blank_vars[key]}" for key in sorted(self.blank_vars.keys())]) + ''.join(self.get_question_body()))
  
  def get_lines(self, output_format: OutputFormat, *args, **kwargs) -> List[str]:
    lines = (
      self.get_header(output_format, *args, **kwargs)
      + self.get_body(output_format, *args, **kwargs)
      + self.get_footer(output_format, *args, **kwargs)
    )
    return lines
  
  def get_question_for_canvas(self, course: canvasapi.course.Course, quiz : canvasapi.quiz.Quiz, *args, **kwargs):
    
    question_text = '<br>\n'.join(self.get_lines(OutputFormat.CANVAS, *args, **kwargs))
    question_text = pypandoc.convert_text(question_text, 'html', format='md')
    
    question_type, answers = self.get_answers(*args, **kwargs)
    return {
      "question_name": f"{self.name} ({datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S.%f')})",
      "question_text": question_text,
      "question_type": question_type.value, #e.g. "fill_in_multiple_blanks"
      "points_possible": 1,
      "answers": answers,
      "neutral_comments_html": pypandoc.convert_text('\n'.join(self.get_explanation(course, quiz)), 'html', format='md')
    }
  
  def get_header(self, output_format : OutputFormat, *args, **kwargs) -> List[str]:
    if output_format == OutputFormat.LATEX:
      return [
        r"\noindent\begin{minipage}{\textwidth}",
        r"\question{" + str(self.value) + r"}",
        r"\noindent\begin{minipage}{0.9\textwidth}",
      ]
    elif output_format == OutputFormat.CANVAS:
      pass
    return []

  def get_footer(self, output_format : OutputFormat, *args, **kwargs) -> List[str]:
    if output_format == OutputFormat.LATEX:
      return [
        r"\end{minipage}",
        r"\end{minipage}"
      ]
    elif output_format == OutputFormat.CANVAS:
      pass
    return []

  @staticmethod
  def get_table_lines(
      table_data: Dict[str,List[str]],
      headers: List[str] = None,
      sorted_keys: List[str] = None,
      add_header_space: bool = False,
      hide_keys: bool = False
  ) -> List[str]:
    
    if headers is None: headers = []
    
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
  def from_yaml(cls, path_to_yaml):
    with open(path_to_yaml) as fid:
      question_dicts = yaml.safe_load_all(fid)
      log.debug(pprint.pformat(list(question_dicts)))
  
  @abc.abstractmethod
  def get_body(self, *args, **kwargs) -> List[str]:
    pass
  
  def get_explanation(self, *args, **kwargs) -> List[str]:
    log.warning("get_explanation using default empty implementation!  Consider implementing!")
    return []
  
  def get_answers(self, *args, **kwargs) -> Tuple[Answer.AnswerKind, List[Dict[str,Any]]]:
    log.warning("get_answers using default empty implementation!  Consider implementing!")
    return Answer.AnswerKind.BLANK, []


class Question_legacy(Question):
  _jinja_env = None
  
  def __init__(self, name: str, value: float, kind: Question.TOPIC, text: str, *args, **kwargs):
    super().__init__(name, value, kind, *args, **kwargs)
    self.text = text
    
    if self._jinja_env is None:
      self._jinja_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader("templates"),
        block_start_string='<BLOCK>',
        block_end_string='</BLOCK>',
        variable_start_string='<VAR>',
        variable_end_string='</VAR>',
        comment_start_string='<COMMENT>',
        comment_end_string='</COMMENT>',
      )
      functions = [method for name, method in inspect.getmembers(QuickFunctions, lambda m: inspect.ismethod(m))]
      for func in functions:
        self._jinja_env.globals[func.__name__] = getattr(QuickFunctions, func.__name__)
  
  def get_body(self, output_format: OutputFormat, *args, **kwargs) -> List[str]:
    lines = []
    if output_format == OutputFormat.LATEX:
      lines.extend([
        self._jinja_env.from_string(self.text.replace("[answer]", "\\answerblank{3}")).render().replace('[', '{[').replace(']', ']}')
      ])
      if self.extra_attrs.get("clear_page", False):
        lines.append(r"\vspace{10cm}")
    elif output_format == OutputFormat.CANVAS:
      lines.extend([
        self._jinja_env.from_string(self.text).render().replace(r"\answerblank{3}", "[answer]"),
      ])
  
    return lines
  
  def get_answers(self, *args, **kwargs) -> Tuple[str, List[Dict[str,Any]]]:
    answers = []
    answers.append({
      "blank_id": "answer",
      "answer_text": "variation",
      "answer_weight": 100,
    })
    return "fill_in_multiple_blanks_question", answers
  
  
  @classmethod
  def from_yaml(cls, path_to_yaml):
    questions = []
    with open(path_to_yaml) as fid:
      question_dicts = yaml.safe_load_all(fid)
      for question_dict in question_dicts:
        log.debug(question_dict)
        if not question_dict.get("enabled", True):
          continue
        extra_attrs = {
          key : question_dict[key]
          for key in question_dict.keys()
          if key not in ["value", "kind", "text", "name"]
        }
        repeat = question_dict.get("repeat", 1)
        for _ in range(repeat):
          questions.append(
            cls(
              name=question_dict.get("name", "(question)"),
              value=question_dict["value"],
              kind=Question.TOPIC.from_string(question_dict["subject"]),
              text=question_dict["text"],
              # **extra_attrs
            )
          )
    return questions
  
  def get_explanation(self, *args, **kwargs) -> List[str]:
    return []