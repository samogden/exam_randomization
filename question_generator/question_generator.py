#!env python
import argparse
import datetime
import os.path
import random
import subprocess
import sys
import time
from typing import List, Dict

import textwrap

import inspect
import importlib

import text2qti.quiz

import math_questions


import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

from process_questions import SchedulingQuestion

def get_flags():
  parser = argparse.ArgumentParser()
  
  parser.add_argument("--num_variations", default=200)
  parser.add_argument("--points_per_question", default=1)
  
  return parser.parse_args()
  


def generate_quiz(quiz_name:str, module_names:List[str], num_variations_per_class=1, group_variations=True, question_classes=None, points_per_question=1, **kwargs):
  
  
  def get_classes(module):
    logging.debug([name for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and obj.__module__ == module.__name__])
    return [(obj, name) for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and obj.__module__ == module.__name__ and (question_classes is not None and name in question_classes)]
  
  generation_time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
  markdown_text = textwrap.dedent(
    f"""
      Quiz title: {quiz_name}-{generation_time}
      shuffle answers: true
      
      """
  )
  
  for module_name in module_names:
    module = importlib.import_module(module_name)
    for (c, name) in get_classes(module):
      
      if "num_to_pick" in question_classes[name]:
        num_to_pick = question_classes[name]
      else:
        num_to_pick = 1
      
      if "variations" in question_classes[name]:
        variations = question_classes[name]["variations"]
      else:
        variations = [{"kwargs" : {}}]
        
      for variation in variations:
        module_kwargs = variation["kwargs"]
        logging.debug(f"{c} : {module_kwargs}")
        markdown_text += c.generate_group_markdown(
          num_variations=num_variations_per_class,
          points_per_question=1,
          num_to_pick=num_to_pick,
          module_kwargs=module_kwargs
        )
        markdown_text += "\n\n"
  
  markdown_file_name = '-'.join(quiz_name.split(' ')) + "-" + generation_time + ".md"
  # if not os.path.exists("./"): os.mkdir("output")
  with open(os.path.join("./", markdown_file_name), 'w') as fid:
    fid.write(markdown_text)
  
  return os.path.join("./", markdown_file_name)
  

def main():
  
  
  flags = get_flags()
  modules = [
    "math_questions",
    "memory_questions",
    "process_questions",
    "language_questions"
  ]
  
  markdown_file = generate_quiz("Mixed Quiz", modules, num_variations_per_class=flags.num_variations,
    question_classes = {
      # "BitsAndBytes" : {},
      # "HexAndBinary" : {},
      # "BaseAndBounds" : {},
      # "Paging" : {},
      # "Paging_with_table" : {},
      
      "SchedulingQuestion" : {
        "variations" : [
          { "kwargs" : {
            "kind" : enum_var,
            "num_jobs": 3,
            "max_arrival_time": 10,
            "min_duration": 4,
            "max_duration": 10,
          } } for enum_var in list(SchedulingQuestion.Kind)
        ]
      },
      #
      # "BNFQuestion_rewriting_left_recursion" : {},
      # "BNFQuestion_rewriting_left_factoring" : {},
      # "BNFQuestion_rewriting_nonterminal_expansion" : {},
      
      # "BNFQuestion_generation" : {
      #   "variations" : [
      #     { "kwargs" : { "switch" : num} } for num in range(3)
      #   ]
      # },
    },
    points_per_question=flags.points_per_question
  )
  subprocess.Popen(f"text2qti {markdown_file}", shell=True)
  
  return



if __name__ == "__main__":
  main()
