#!env python
from __future__ import annotations

import base64
import io
import itertools
import json
import logging
import os
import random
from typing import List

import PIL.Image
import pymupdf as fitz
import requests

from question import Question
from misc import get_file_list

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Assignment():
  
  _id_counter = itertools.count()  # create an iterator that returns consecutive integers
  
  def __init__(self, input_pdf: str, question_locations: List[QuestionLocation], question_margin=10):
    self.id = next(self._id_counter)  # get the next unique id
    self.input_pdf = input_pdf
    self.pdf_doc = fitz.open(self.input_pdf)
    self.page_scores = {i: None for i in range(self.pdf_doc.page_count)}
    
    self.questions: List[Question] = []
    for (page_number, page) in enumerate(self.pdf_doc):
      page_width = page.rect.width
      page_height = page.rect.height
      
      log.debug(f"On page {page_number}...")
      questions_on_page = list(filter((lambda ql: ql.page_number == page_number), question_locations))
      
      for (q_start, q_end) in zip(questions_on_page, questions_on_page[1:] + [None]):
        log.debug(f"isolating {q_start.question_number}")
        if q_end is None:
          question_rect = fitz.Rect(0, q_start.location - question_margin, page_width, page_height)
        else:
          question_rect = fitz.Rect(0, q_start.location, page_width - question_margin, q_end.location + question_margin)
        question_pixmap = page.get_pixmap(matrix=fitz.Matrix(1, 1), clip=question_rect)
        self.questions.append(
          Question(q_start.question_number, PIL.Image.open(io.BytesIO(question_pixmap.tobytes())))
        )
        log.debug(f"stored q{self.questions[-1].number}")
      self.questions = sorted(self.questions, key=(lambda q: q.number))
      log.debug(f"num question: {len(self.questions)}")
  
  def __str__(self):
    return f"Submission_{self.id}({self.pdf_doc.page_count})"
  
  def get_page(self, page_number) -> fitz.Page:
    return self.pdf_doc[page_number]
  
  @classmethod
  def read_directory(cls, path_to_directory, base_exam, shuffle=True) -> List[Assignment]:
    files = get_file_list(os.path.expanduser(path_to_directory))
    for f in files:
      if ".DS_Store" in f:
        os.remove(f)
        files.remove(f)
    
    question_locations = QuestionLocation.get_question_locations(base_exam)
    submissions = [
      Assignment(f, question_locations)
      for f in files
    ]
    
    if shuffle:
      random.shuffle(submissions)
    
    return submissions
  
  
class QuestionLocation():
  def __init__(self, question_number, page_number, location):
    self.question_number = question_number
    self.page_number = page_number
    self.location = location
    # todo: add in a reference snippet
  
  @staticmethod
  def get_question_locations(base_exam: str) -> List[QuestionLocation]:
    question_locations = []
    
    pdf_doc = fitz.open(base_exam)
    for page_number, page in enumerate(pdf_doc.pages()):
      # log.debug(f"Looking on {page_number}")
      for question_number in range(30):
        text_instances = page.search_for(f"Question {question_number}:")
        if len(text_instances) > 0:
          # log.debug(f"Found question {question_number}")
          question_locations.append(QuestionLocation(question_number, page_number, text_instances[0].tl.y))
    
    return question_locations

  
  

