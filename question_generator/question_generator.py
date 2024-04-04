#!env python
import argparse
import datetime
import random
import sys
import time
from typing import List

import textwrap

import inspect
import importlib
import math_questions


import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

def get_flags():
  parser = argparse.ArgumentParser()
  
  parser.add_argument("--num_variations", default=100)
  parser.add_argument("--points_per_question", default=2)
  
  return parser.parse_args()
  


def generate_quiz(name:str, modules:List[str], num_variations_per_class=1, group_variations=True):
  
  def get_classes(module):
    return [obj for name, obj in inspect.getmembers(module) if inspect.isclass(obj) and obj.__module__ == module.__name__]
  
  
  with open('-'.join(name.split(' ')) + ".md", 'w') as fid:
    
    fid.write(
      textwrap.dedent(
        f"""
        Quiz title: {name}
        Quiz description: trying out some new generation things
        
        """
      )
    )
  
    for module in modules:
      m = importlib.import_module(module)
      for c in get_classes(m):
        if "MemoryAccessQuestion" in c.__name__: continue # todo: fix this hack
        logging.debug(c)
        fid.write(c.generate_group_markdown(num_variations=num_variations_per_class, points_per_question=2))
        fid.write("\n\n")


def main():
  
  
  flags = get_flags()
  modules = [
    "math_questions",
    "memory_questions",
    # "process_questions"
  ]
  
  generate_quiz("Mixed Quiz", modules)
  
  return



if __name__ == "__main__":
  main()
