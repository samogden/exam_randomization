#!env python
from __future__ import annotations

import json
import logging
import math
import random
from typing import List, Dict

import jinja2
import inspect
import re

from exam_generation_functions import QuickFunctions

import yaml

class QuestionSet():
  def __init__(self, questions_file):
    
    self.env = jinja2.Environment(
      block_start_string='<BLOCK>',
      block_end_string='</BLOCK>',
      variable_start_string='<VAR>',
      variable_end_string='</VAR>',
      comment_start_string='<COMMENT>',
      comment_end_string='</COMMENT>',
    )
    
    functions = [method for name, method in inspect.getmembers(QuickFunctions, lambda m: inspect.ismethod(m))]
    for func in functions:
      self.env.globals[func.__name__] = getattr(QuickFunctions, func.__name__)
    self.questions = self.load_questions(questions_file)
  
  def load_questions(self, questions_file: str|List[str]) -> List[Question]:
    
    if not isinstance(questions_file,str): # todo: hackity-hack-hack
      questions = []
      for f in questions_file:
        questions.extend(self.load_questions(f))
      return questions
    
    if questions_file.endswith(".json"):
      questions_list = self.load_from_json(questions_file)
    elif questions_file.endswith(".yaml") or questions_file.endswith(".yml"):
      if isinstance(questions_file, str):
        questions_list = self.load_from_yaml(questions_file)
    else:
      logging.error("Question file in unsupported format.  Please provide either JSON or YAML")
      return []
  
    
    questions = []
    for question in questions_list:
      if "enabled" in question and not question["enabled"]:
        continue
    
      if "answer_func" in question:
        exec(question["answer_func"], globals())
        answer_func = get_answer
      else:
        answer_func = (lambda *args : None)
      
      if "clear_page" in question:
        clear_page = question["clear_page"]
      else:
        clear_page = False
      
      if "repeat" in question:
        repeat = question["repeat"]
      else:
        repeat = 1
      for _ in range(repeat):
        questions.append(
          Question(
            question["value"],
            question["text"],
            subject=question["subject"],
            env=self.env,
            answer_func=answer_func,
            clear_page=clear_page,
          )
        )
    return questions
  
  @classmethod
  def load_from_json(cls, questions_file) -> List[Dict]:
    with open(questions_file) as fid:
      questions_dict = json.load(fid)
    questions_list = questions_dict["questions"]
    for q in questions_list:
      q["text"] = ' \n'.join([
          re.sub(
            r'\[[\w_][\w_]+\]',
            "\\\\answerblank{3}",
            line
          ) #.replace('[', '{[').replace(']', ']}')
          for line in q["lines"]
        ])
    return questions_list
    
  @classmethod
  def load_from_yaml(cls, questions_file) -> List[Dict]:
    with open(questions_file) as fid:
      loaded_questions = list(yaml.load_all(fid, Loader=yaml.SafeLoader))
    if isinstance(loaded_questions, list):
      return loaded_questions
    else:
      return [loaded_questions]
    

class Question():
  
  def __init__(self, value, question_text, env=None, clear_page=False, *args, **kwargs):
    self.value = value
    self.text = question_text
    self.subject = None if "subject" not in kwargs else kwargs["subject"]
    self.env = env
    self.clear_page = clear_page
    
    self.args = args
    self.kwargs = kwargs
  
  
  def fill_in(self, env):
    text = self.text.replace("[answer]", "\\answerblank{3}")
    # text = re.sub(
    #   r'\[answer\]',
    #   "\\\\answerblank{3}",
    #   self.text
    # )
    logging.debug(f"text: {text}")
    template = env.from_string(text)
    return template.render()
  
  def get_question(self, env):
    return f"\\question{{{self.value}}}{{\n{self.fill_in(env).replace('[', '{[').replace(']', ']}')}\n}}"
  
  def generate_latex(self, is_first=False):
    return_str = f"\\question{{{self.value}}}{{\n{self.fill_in(self.env).replace('[', '{[').replace(']', ']}')}\n}}"
    if self.clear_page:
      if is_first:
        return_str = return_str + "\\newpage"
      else:
        return_str = "\\newpage" + return_str + "\\newpage"
      
      # if not is_first:
      #   return_str += "\\newpage" + return_str + "\\newpage"
      # else :
      # return_str = return_str + "\\newpage"
    
    return return_str
  

if __name__ == "__main__":
  logging.getLogger().setLevel(logging.DEBUG)
  
  question_set = QuestionSet("templates/questions.yaml")
  logging.debug(question_set)
  