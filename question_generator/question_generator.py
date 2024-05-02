#!env python
import argparse
import datetime
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
  
  parser.add_argument("--num_variations", default=10)
  parser.add_argument("--points_per_question", default=1)
  
  return parser.parse_args()
  


def generate_quiz(quiz_name:str, module_names:List[str], num_variations_per_class=1, group_variations=True, question_classes=None, **kwargs):
  
  
  def get_classes(module):
    logging.debug([name for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and obj.__module__ == module.__name__])
    return [(obj, name) for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and obj.__module__ == module.__name__ and (question_classes is not None and name in question_classes)]
  
  generation_time = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
  markdown_text = textwrap.dedent(
    f"""
      Quiz title: {quiz_name}-{generation_time}
      
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
          points_per_question=2,
          num_to_pick=num_to_pick,
          module_kwargs=module_kwargs
        )
        markdown_text += "\n\n"
      #
      #
      # if "kwargs" in question_classes[name]:
      #   module_kwargs = question_classes[name]["kwargs"]
      # else:
      #   module_kwargs = {}
      #
      # logging.debug(c)
      # markdown_text += c.generate_group_markdown(
      #   num_variations=num_variations_per_class,
      #   points_per_question=2,
      #   num_to_pick=num_to_pick,
      #   module_kwargs=module_kwargs
      # )
      # markdown_text += "\n\n"
  
  markdown_file_name = '-'.join(quiz_name.split(' ')) + "-" + generation_time + ".md"
  with open(markdown_file_name, 'w') as fid:
    fid.write(markdown_text)
  
  return markdown_file_name
  

def main():
  
  
  flags = get_flags()
  modules = [
    # "math_questions",
    "memory_questions",
    "process_questions"
  ]
  
  markdown_file = generate_quiz("Mixed Quiz", modules, num_variations_per_class=flags.num_variations,
    question_classes = {
      # "BaseAndBounds" : 1,
      # "Paging_with_table" : 1,
      "SchedulingQuestion" : {
        "variations" : [
          { "kwargs" : { "kind" : enum_var} } for enum_var in list(SchedulingQuestion.Kind)
          # { "kwargs" : { "kind" : SchedulingQuestion.Kind.RoundRobin} },
          # { "kwargs" : { "kind" : SchedulingQuestion.Kind.ShortestDuration} },
          # { "kwargs" : { "kind" : SchedulingQuestion.Kind.ShortestTimeRemaining} },
          # { "kwargs" : { "kind" : SchedulingQuestion.Kind.FIFO} },
        ]
      },
    }
  )
  subprocess.Popen(f"text2qti {markdown_file}", shell=True)
  
  return



if __name__ == "__main__":
  main()
