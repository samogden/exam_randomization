#!env python
import argparse
import datetime
import random
import subprocess
import sys
import time
from typing import List

import textwrap

import inspect
import importlib

import text2qti.quiz

import math_questions


import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

def get_flags():
  parser = argparse.ArgumentParser()
  
  parser.add_argument("--num_variations", default=2)
  parser.add_argument("--points_per_question", default=2)
  
  return parser.parse_args()
  


def generate_quiz(name:str, modules:List[str], num_variations_per_class=1, group_variations=True, allowed_classes=None):
  
  def get_classes(module):
    logging.debug([name for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and obj.__module__ == module.__name__])
    return [obj for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and obj.__module__ == module.__name__ and (allowed_classes is not None and name in allowed_classes)]
  
    
  markdown_text = textwrap.dedent(
    f"""
      Quiz title: {name}
      
      """
  )
  
  for module in modules:
    m = importlib.import_module(module)
    for c in get_classes(m):
      if "MemoryAccessQuestion" in c.__name__: continue # todo: fix this hack
      
      logging.debug(c)
      markdown_text += c.generate_group_markdown(num_variations=num_variations_per_class, points_per_question=2)
      markdown_text += "\n\n"
      # fid.write(c.generate_group_markdown(num_variations=num_variations_per_class, points_per_question=2))
      # fid.write("\n\n")
  
  markdown_file_name = '-'.join(name.split(' ')) + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + ".md"
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
    allowed_classes=[
      "BaseAndBounds",
      "Paging_with_table",
      "SchedulingQuestion"
    ]
  )
  subprocess.Popen(f"text2qti {markdown_file}", shell=True)
  
  return



if __name__ == "__main__":
  main()
