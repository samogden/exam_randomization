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
import tkinter as tk
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

  def get_tkinter_frame(self, parent) -> tk.Frame:
    frame = tk.Frame(parent)
    
    # Make a scrollbar for the Listbox
    question_scrollbar = tk.Scrollbar(frame)
    question_scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)
    
    # Make a Listbox for questions
    question_listbox = tk.Listbox(frame, yscrollcommand=question_scrollbar.set)
    for i, q in enumerate(self.questions):
      question_listbox.insert(i, q)
    question_listbox.pack()
    question_listbox.focus()
    
    def doubleclick_callback(_):
      log.info(f"x: {question_listbox.selection_get()}")
    
    # Set up a callback for double-clicking
    question_listbox.bind('<Double-1>', doubleclick_callback)
    
    frame.pack()
    return frame
    

class ScannedExam(Assignment):
  def __init__(self, path_to_base_exam, path_to_scanned_exams, limit=None):
    files = [os.path.join(f) for f in get_file_list(path_to_scanned_exams) if f.endswith(".pdf")]
    
    if limit is not None:
      files = files[:limit]
    
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
