#!env python
import json
import logging
import math
import random

import jinja2
import inspect
import re

class QuestionSet():
  def __init__(self, questions_file="questions.json"):
    
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
      print(func)
      self.env.globals[func.__name__] = getattr(QuickFunctions, func.__name__)
    
    self.questions = self.load_from_json(self.env, questions_file)
  
  @classmethod
  def load_from_json(cls, env, questions_file="questions.json"):
    with open(questions_file) as fid:
      questions_dict = json.load(fid)
    
    questions = []
    for question in questions_dict["questions"]:
      if "enabled" in question and not question["enabled"]: continue
      questions.append(
        Question(
          question["value"],
          # ' \\\\\n'.join([
          ' \n'.join([
            re.sub(
              r'\[[\w_][\w_]+\]',
              "\\\\answerblank{3}",
              line
            ) #.replace('[', '{[').replace(']', ']}')
            for line in question["lines"]
          ]),
          env,
          subject=question["subject"]
        )
      )
    
    return questions

class Question():
  
  def __init__(self, value, question_text, env, *args, **kwargs):
    self.value = value
    self.text = question_text
    self.subject = None if "subject" not in kwargs else kwargs["subject"]
    self.env = env
    self.args = args
    self.kwargs = kwargs
  
  
  def fill_in(self):
    logging.debug(f"self.text: {self.text}")
    template = self.env.from_string(self.text)
    return template.render()
  
  def get_question(self):
    return f"\\question{{{self.value}}}{{\n{self.fill_in().replace('[', '{[').replace(']', ']}')}\n}}"
  

class QuickFunctions:
  
  @classmethod
  def add_spaces_to_str(cls, input_str, every=4):
    if len(input_str) < 2*every:
      return input_str
    return ' '.join([input_str[i:i+every] for i in range(0, len(input_str), every)])
  
  @classmethod
  def random_binary_number(cls, num_bits):
    return random.randrange(0, int(math.pow(2, num_bits)))
    return '0b ' + cls.add_spaces_to_str(cls.random_binary_bits(num_bits))
  
  @classmethod
  def random_binary_bits(cls, num_bits):
    return ''.join(random.choices("01", k=num_bits))
  @classmethod
  def random_hex_number(cls, num_digits):
    return '0x' + cls.random_hex_digits(num_digits)
  
  @classmethod
  def random_hex_digits(cls, num_digits):
    return ''.join(random.choices("0123456789abcdef".upper(), k=num_digits))
  
  @classmethod
  def pick_replacement_algo(cls):
    return cls.pick_a_choice(["LRU", "FIFO", "Belady"])
  
  @classmethod
  def pick_a_choice(cls, list_of_choices):
    return str(random.choice(list_of_choices))
  
  @classmethod
  def number_in_range(cls, lower_bound, upper_bound):
    return random.randrange(lower_bound, upper_bound)
  
  @classmethod
  def print_as_hex(cls, in_number, pad_to_length=0, show_prefix=True, add_spaces=False):
    out_str = f"{in_number : x}".zfill(pad_to_length)
    if add_spaces:
      out_str = ' ' + cls.add_spaces_to_str(out_str)
    if show_prefix:
      out_str = '0x' + out_str
    return out_str
  
  @classmethod
  def print_as_binary(cls, in_number, pad_to_length=0, show_prefix=True, add_spaces=False, every=4):
    out_str = f"{in_number : b}".zfill(pad_to_length)
    if add_spaces:
      out_str = ' ' + cls.add_spaces_to_str(out_str)
    if show_prefix:
      out_str = '0b' + out_str
    return out_str