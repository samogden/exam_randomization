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
import tkinter
from typing import List
import io
import dotenv

import PIL.Image
import PIL.ImageTk
import pymupdf as fitz
import requests

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def parse_flags():
  parser = argparse.ArgumentParser()
  
  parser.add_argument("--input_dir", default="~/Documents/CSUMB/grading/CST334/2024Spring/Exam3/00-base")
  parser.add_argument("--query_ai", action="store_true")
  parser.add_argument("--base_exam", default="../exam_generation/exam.pdf")
  
  parser.add_argument("--debug", action="store_true")
  
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
  class QuestionLocation():
    def __init__(self, question_number, page_number, location):
      self.question_number = question_number
      self.page_number = page_number
      self.location = location
    
  class Question():
    def __init__(self, *args, **kwargs):
      pass
  
  _id_counter = itertools.count()  # create an iterator that returns consecutive integers
  
  def __init__(self, input_pdf: str, question_locations: List[QuestionLocation], question_margin=10):
    self.id = next(self._id_counter)  # get the next unique id
    self.input_pdf = input_pdf
    self.pdf_doc = fitz.open(self.input_pdf)
    self.page_scores = {i: None for i in range(self.pdf_doc.page_count)}
    
    for (page_number, page) in enumerate(self.pdf_doc):
      page_width = page.rect.width
      page_height = page.rect.height
      
      log.debug(f"On page {page_number}...")
      questions_on_page = list(filter((lambda ql: ql.page_number == page_number), question_locations))
      
      for (q_start, q_end) in zip(questions_on_page, questions_on_page[1:] + [None]):
      
      # for question_location in questions_on_page:
        log.debug(f"isolating {q_start.question_number}")
        if q_end is None:
          question_rect = fitz.Rect(0, q_start.location-question_margin, page_width, page_height)
        else:
          question_rect = fitz.Rect(0, q_start.location, page_width-question_margin, q_end.location+question_margin)
        question_pixmap = page.get_pixmap(matrix=fitz.Matrix(1,1), clip=question_rect)
        question_pixmap.save(f"q{q_start.question_number}.png")
  
  def grading_complete(self):
    return not any([v is None for v in self.page_scores.values()])
  
  def __str__(self):
    return f"Submission_{self.id}({self.pdf_doc.page_count})"
  
  def get_page(self, page_number) -> fitz.Page:
    return self.pdf_doc[page_number]


def do_grading_pass(submissions: List[Submission], page_number, query_ai, flags):
  for submission in sorted(submissions, key=(lambda _: random.random())):
    log.debug(f"Looking at {submission}")
    page = submission.get_page(page_number)
    
    page = submission.get_page(page_number)
    
    pix = page.get_pixmap()
    img_bytes = pix.pil_tobytes(format="PNG")
    img = PIL.Image.open(io.BytesIO(img_bytes))
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    
    if query_ai:
      get_chat_gpt_response(img_base64)
    show_gui(page)
    
    if not flags.debug:
      got_score = False
      while not got_score:
        try:
          page_score = int(input("Page score: "))
          got_score = True
        except ValueError:
          pass
      submission.page_scores[page_number] = page_score


def show_gui(page: fitz.Page):
  root = tkinter.Tk()
  
  pix = page.get_pixmap()
  img_bytes = pix.pil_tobytes(format="PNG")
  img = PIL.Image.open(io.BytesIO(img_bytes))
  
  photo = PIL.ImageTk.PhotoImage(img)
  image_label = tkinter.Label(root, image=photo)
  image_label.image = photo
  image_label.grid(row=0, column=0, padx=10, pady=10)
  root.mainloop()


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
            "text": "Please grade this page from an exam for me.  Please give response as a JSON dictionary with keys \"awarded points\", \"possible points\" and \"explanation\"."
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




def get_question_locations(base_exam: str) -> List[Submission.QuestionLocation]:
  question_locations = []
  
  pdf_doc = fitz.open(base_exam)
  for page_number, page in enumerate(pdf_doc.pages()):
    # log.debug(f"Looking on {page_number}")
    for question_number in range(30):
      text_instances = page.search_for(f"Question {question_number}:")
      if len(text_instances) > 0:
        # log.debug(f"Found question {question_number}")
        question_locations.append(Submission.QuestionLocation(question_number, page_number, text_instances[0].tl.y))
  
  return question_locations


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
  
  if flags.debug:
    question_locations = get_question_locations(flags.base_exam)
    submission = Submission(random.choice(files), question_locations)
    show_gui(submission.pdf_doc[0])
    
    # show_gui(page)
    return
  
  submissions = [
    Submission(f)
    for f in sorted(files, key=lambda _: random.random())[:1]
  ]
  
  
  for page_number in sorted(range(submissions[0].pdf_doc.page_count), key=(lambda _: random.random())):
    do_grading_pass(submissions, page_number, flags.query_ai, flags)
    break
  
  for submission in submissions:
    log.info(f"{submission} : {sum(filter(lambda v: v is not None, submission.page_scores.values()))}")


if __name__ == "__main__":
  main()
