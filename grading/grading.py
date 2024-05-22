#!env python

import argparse
import base64
import collections
import itertools
import logging
import math
import os
import pathlib
import random
import shutil
from typing import List
import io
import dotenv

import PIL.Image
import pymupdf as fitz
import requests

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def parse_flags():
  parser = argparse.ArgumentParser()
  
  parser.add_argument("--input_dir", default="~/Documents/CSUMB/grading/CST334/2024Spring/Exam3/00-base")
  
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

class Submission():
  _id_counter = itertools.count()  # create an iterator that returns consecutive integers

  def __init__(self, input_pdf : str):
    self.id = next(self._id_counter)  # get the next unique id
    self.input_pdf = input_pdf
    self.pdf_doc = fitz.open(self.input_pdf)
    self.page_scores = { i : 0 for i in range(self.pdf_doc.page_count)}
      
    
  def __str__(self):
    return f"Submission_{self.id}({self.pdf_doc.page_count})"
  
  def get_page(self, page_number) -> fitz.Page:
    for i, p in enumerate(self.pdf_doc):
      if i == page_number:
        return p
    return self.pdf_doc[page_number]

def do_grading_pass(submissions: List[Submission], page_number):
  for submission in sorted(submissions, key=(lambda _: random.random())):
    log.debug(f"Looking at {submission}")
    page = submission.get_page(page_number)
    
    # Next few lines from ChatGPT
    # page.get_
    page = submission.get_page(page_number)
    
    pix = page.get_pixmap()
    img_bytes = pix.pil_tobytes(format="PNG")
    
    # Encode the PNG image in base64
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    
    img = PIL.Image.open(io.BytesIO(img_bytes))
    img.show()
    
    get_chat_gpt_response(img_base64)

def get_chat_gpt_response(base64_png):
  headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
  }

  payload = {
    "model": "gpt-4o",
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text": "Please grade this page from an exam for me.  Please give response as a JSON string with keys \"awarded points\", \"possible points\" and \"explanation\"."
          },
          {
            "type": "image_url",
            "image_url": {
              "url": f"data:image/png;base64,{base64_png}"
            }
          }
        ]
      }
    ],
    "max_tokens": 300
  }
  
  response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
  log.debug(response.json()["choices"][0]["message"]["content"])



def main():
  flags = parse_flags()
  dotenv.load_dotenv()
  
  if flags.input_dir is None:
    logging.error("Please specify input directory")
    return
  files = get_file_list(os.path.expanduser(flags.input_dir))
  for f in files:
    if ".DS_Store" in f:
      os.remove(f)
      files.remove(f)
  
  submissions = [
    Submission(f)
    for f in sorted(files,key=lambda _: random.random())[:1]
  ]
  
  print(submissions)
  do_grading_pass(submissions, 1)
  
if __name__ == "__main__":
  main()
