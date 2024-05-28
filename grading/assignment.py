#!env python
from __future__ import annotations

import base64
import collections
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

import question

# from question import Response_fromPDF as Question, Response_fromPDF, Response
from misc import get_file_list

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class Assignment:
  """
  An assignment is an indvidual assignment that will contain a number of Questions, each of which contain a number of Responses.
  This will better match the structure of real assignments, and thus be flexible for different sources.
  """
  
  def __init__(self, questions: List[question.Question]):
    self.questions = questions
  
  def __str__(self):
    return f"Assignment({len(self.questions)}questions, {sum([q.max_points for q in self.questions])}points)"
    
  def get_by_student(self):
    # todo: after grading this function can be used ot get a by-student representation of the questions
    pass

class ScannedExam(Assignment):
  def __init__(self, path_to_base_exam, path_to_scanned_exams):
    files = [os.path.join(f) for f in get_file_list(path_to_scanned_exams) if f.endswith(".pdf")]
    
    question_locations = QuestionLocation.get_question_locations(path_to_base_exam)
    
    question_responses : collections.defaultdict[int,List[question.Response]] = collections.defaultdict(list)
    
    # Break up each pdf into the responses
    for student_id, f in enumerate(files):
      log.info(f"Loading student {student_id+1}/{len(files)}")
      for question_number, response in question.Response_fromPDF.load_from_pdf(student_id, f, question_locations).items():
        question_responses[question_number].append(response)
    
    
    # Make questions from each response
    questions = [
      question.Question(question_number, responses)
      for (question_number, responses) in question_responses.items()
    ]
      
    super().__init__(questions)


class Assignment_old:
  """
  This is more similar to a "Submission" in the new restructuring
  """
  
  _id_counter = itertools.count()  # create an iterator that returns consecutive integers
  
  def __init__(self, input_pdf: str, question_locations: List[QuestionLocation], question_margin=10):
    self.id = next(self._id_counter)  # get the next unique id
    self.input_pdf = input_pdf
    self.pdf_doc = fitz.open(self.input_pdf)
    self.page_scores = {i: None for i in range(self.pdf_doc.page_count)}
    
    self.questions: List[question.Question] = []
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
          question.Question(q_start.question_number, PIL.Image.open(io.BytesIO(question_pixmap.tobytes())))
        )
        log.debug(f"stored q{self.questions[-1].question_number}")
      self.questions = sorted(self.questions, key=(lambda q: q.question_number))
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
  def get_question_locations(path_to_base_exam: str) -> List[QuestionLocation]:
    question_locations = []
    
    pdf_doc = fitz.open(path_to_base_exam)
    for page_number, page in enumerate(pdf_doc.pages()):
      # log.debug(f"Looking on {page_number}")
      for question_number in range(30):
        text_instances = page.search_for(f"Question {question_number}:")
        if len(text_instances) > 0:
          question_locations.append(QuestionLocation(question_number, page_number, text_instances[0].tl.y))
    
    return question_locations
