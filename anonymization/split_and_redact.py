#!env python
import argparse
import logging
import math
import os
import pathlib
import random
import shutil
from typing import List
import fitz


logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def parse_flags():
  parser = argparse.ArgumentParser()
  
  parser.add_argument("--input_dir", required=True)
  parser.add_argument("--leave_name", dest="override_name", action="store_false")
  parser.add_argument("--base", default=0, type=int)
  
  parser.add_argument("--testing", action="store_true")
  
  return parser.parse_args()



def get_file_list(dir_to_deduplicate) -> List[str]:
  dir_to_deduplicate = os.path.expanduser(dir_to_deduplicate)
  return list(
    filter(
      (lambda f: not os.path.isdir(f) and not f.endswith(".part")),
      [
        os.path.join(dir_to_deduplicate, f)
        for f in os.listdir(dir_to_deduplicate)
      ]
    )
  )

def add_randomization(files, separator=" - ", out_dir="randomized", override_name=False, base=0) -> List[str]:
  new_names = []
  directory = out_dir
  for i, f in enumerate(random.sample(files, len(files))):
    stem = pathlib.Path(f).name
    new_path = os.path.join(directory, f"{str(i+base).zfill(int(math.log10(len(files)+base) + 1))}{separator}{stem}")
    if override_name:
      new_path = os.path.join(directory, f"{str(i+base).zfill(int(math.log10(len(files)+base) + 1))}.{stem.split('.')[-1]}")
    
    log.debug(f"{f} -> {new_path}")
    shutil.copy(f, new_path)
    new_names.append(new_path)
  return new_names


def redact_directory(input_directory, output_directory):
  for f in [os.path.join(input_directory, f) for f in os.listdir(input_directory)]:
    if not f.endswith(".pdf"): continue
    doc = fitz.open(f)
    for page in doc:
      # For every page, draw a rectangle on coordinates (1,1)(100,100)
      page.draw_rect([370,100,500,150],  color = (0, 0, 0), width = 50)
      break
    # Save pdf
    doc.save(f"{os.path.join(output_directory,pathlib.Path(f).name)}")
    doc.close()


def main():
  flags = parse_flags()
  
  files = get_file_list(os.path.expanduser(flags.input_dir))
  for f in files:
    if ".DS_Store" in f:
      os.remove(f)
      files.remove(f)
  
  if flags.testing:
    return
  
  def clean_dir(directory):
    shutil.rmtree(directory, ignore_errors=True)
    os.mkdir(directory)
  clean_dir("randomized")
  clean_dir("redacted")
  
  files = add_randomization(files, override_name=flags.override_name, out_dir="randomized", base=flags.base)
  redact_directory("randomized", "redacted")
  

if __name__ == "__main__":
  main()
