#!env python

from __future__ import annotations


import abc
import enum
import inspect
import pprint
import yaml
from typing import List
import jinja2

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


from exam_generation_functions import QuickFunctions


class Question(abc.ABC):
  """
  A question base class that will be able to output questions to a variety of formats.
  """
  
  # todo: when calculating hash, have an attribute "max repeats" that will return the hash with a field that will stop changing after a certain number of repeats
  
  class KIND(enum.Enum):
    PROCESS = enum.auto()
    MEMORY = enum.auto()
    THREADS = enum.auto()
    IO = enum.auto()
    PROGRAMMING = enum.auto()
    MISC = enum.auto()
    
    @classmethod
    def from_string(cls, string) -> Question.KIND:
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
  
  def __init__(self, value: float, kind: Question.KIND, *args, **kwargs):
    self.value = value
    self.kind = kind
    
    self.extra_attrs = kwargs # clear page, etc.
    
    # todo: use these
    self.given_vars = {}
    self.target_vars = {}
    self.intermediate_vars = {}
  
  def get_lines(self, *args, **kwargs) -> List[str]:
    return (
      self.get_header(*args, **kwargs)
      + self.get_body(*args, **kwargs)
      + self.get_answer_fields(*args, **kwargs)
      + self.get_footer(*args, **kwargs)
    )
  
  def get_header(self, *args, **kwargs) -> List[str]:
    if kwargs.get("to_latex", False):
      return [
        r"\noindent\begin{minipage}{\textwidth}",
        r"\question{" + str(self.value) + r"}",
        r"\noindent\begin{minipage}{0.9\textwidth}",
      ]
    return []
  def get_body(self, *args, **kwargs) -> List[str]:
    return []
  def get_answer_fields(self, *args, **kwargs) -> List[str]:
    return []
  def get_footer(self, *args, **kwargs) -> List[str]:
    if kwargs.get("to_latex", False):
      return [
        r"\end{minipage}",
        r"\end{minipage}"
      ]
    return []
  
  
  
  @classmethod
  def from_yaml(cls, path_to_yaml):
    with open(path_to_yaml) as fid:
      question_dicts = yaml.safe_load_all(fid)
      log.debug(pprint.pformat(list(question_dicts)))

class Question_legacy(Question):
  _jinja_env = None
  
  def __init__(self, value: float, kind: Question.KIND, text: str, *args, **kwargs):
    super().__init__(value, kind, *args, **kwargs)
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
  
  def get_body(self, *args, **kwargs) -> List[str]:
    
    lines = [
      self._jinja_env.from_string(self.text.replace("[answer]", "\\answerblank{3}")).render().replace('[', '{[').replace(']', ']}')
    ]
    if self.extra_attrs.get("clear_page", False):
      lines.append(r"\vspace{10cm}")
    
    return lines
  
  @classmethod
  def from_yaml(cls, path_to_yaml):
    questions = []
    with open(path_to_yaml) as fid:
      question_dicts = yaml.safe_load_all(fid)
      for question_dict in question_dicts:
        extra_attrs = {
          key : question_dict[key]
          for key in question_dict.keys()
          if key not in ["value", "kind", "text"]
        }
        if "repeat" in question_dict:
          repeat = question_dict["repeat"]
        else:
          repeat = 1
        for _ in range(repeat):
          questions.append(
            cls(
              value=question_dict["value"],
              kind=Question.KIND.from_string(question_dict["subject"]),
              text=question_dict["text"],
              **extra_attrs
            )
          )
    return questions
    