#!env python
import argparse
import collections
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
  
  parser.add_argument("--input_dir", default=None)
  parser.add_argument("--leave_name", dest="override_name", action="store_false")
  parser.add_argument("--base", default=0, type=int)
  
  parser.add_argument("--testing", action="store_true")
  
  parser.add_argument("--remerge", action="store_true")
  
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
    page = doc[0]
    page.draw_rect([360,70,600,110],  color = (0, 0, 0), width = 50)
    
  # Save pdf
    doc.save(f"{os.path.join(output_directory,pathlib.Path(f).name)}")
    doc.close()

def split_by_page(input_directory, output_directory):
  for f in [os.path.join(input_directory, f) for f in os.listdir(input_directory)]:
    if not f.endswith(".pdf"): continue
    doc = fitz.open(f)
    for i in range(doc.page_count):
      page_dir = os.path.join(output_directory, f"{i:0{math.ceil(math.log10(doc.page_count))}}")
      if not os.path.exists(page_dir):
        os.mkdir(page_dir)
      page_doc = fitz.open()
      page_doc.insert_pdf(doc, from_page=i, to_page=i)
      page_doc.save(f"{os.path.join(page_dir, pathlib.Path(f).name)}")
      page_doc.close()
    doc.close()

def merge_pages(input_directory, output_directory):
  exam_pdfs = collections.defaultdict(lambda : fitz.open())
  for page_number in [p for p in sorted(os.listdir(input_directory))]:
    page_number_directory = os.path.join(input_directory, page_number)
    if not os.path.isdir(page_number_directory): continue
    
    print(f"{page_number_directory}")
    for student_pdf in sorted(os.listdir(page_number_directory)):
      student_pdf_path = os.path.join(page_number_directory, student_pdf)
      print(student_pdf_path)
      exam_pdfs[student_pdf].insert_pdf(fitz.open(student_pdf_path))
      
  for student_pdf in exam_pdfs.keys():
    exam_pdfs[student_pdf].save(os.path.join(output_directory, student_pdf))
    

def main():
  flags = parse_flags()
  
  randomized_dir = "01-randomized"
  redacted_dir = "02-redacted"
  by_page_dir = "03-by_page"
  remerge_dir = "04-remerged"
  
  def clean_dir(directory):
    shutil.rmtree(directory, ignore_errors=True)
    os.mkdir(directory)
    
  if not flags.remerge:
    if flags.input_dir is None:
      logging.error("Please specify input directory")
      return
    files = get_file_list(os.path.expanduser(flags.input_dir))
    for f in files:
      if ".DS_Store" in f:
        os.remove(f)
        files.remove(f)
    
    if flags.testing:
      return
    
    clean_dir(randomized_dir)
    clean_dir(redacted_dir)
    clean_dir(by_page_dir)
    
    files = add_randomization(files, override_name=flags.override_name, out_dir=randomized_dir, base=flags.base)
    redact_directory(randomized_dir, redacted_dir)
    split_by_page(redacted_dir, by_page_dir)
  else:
    # then we are merging our pdfs back together
    
    clean_dir(remerge_dir)
    merge_pages(by_page_dir, remerge_dir)
  

if __name__ == "__main__":
  main()
