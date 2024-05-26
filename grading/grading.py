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

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


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
      # todo: add in a reference snippet
  
  class Question():
    def __init__(self, number, img: PIL.Image.Image):
      self.number = number
      self.image = img
      # self.img_base64 = base64.b64encode(img_bytes).decode("utf-8")
      self.grade = None
      self.feedback = None
      self.gpt_response = None
    
    def get_b64(self, format="PNG"):
      # Create a BytesIO buffer to hold the image data
      buffered = io.BytesIO()
      
      # Save the image to the buffer in the specified format
      self.image.save(buffered, format=format)
      
      # Get the byte data from the buffer
      img_byte = buffered.getvalue()
      
      # Encode the byte data to base64
      img_base64 = base64.b64encode(img_byte)
      
      # Convert the base64 byte data to a string
      img_base64_str = img_base64.decode('utf-8')
      
      return img_base64_str
  
    def __str__(self):
      return f"{self.number}({self.grade})"

    def get_chat_gpt_response(self, question : Submission.Question, max_tokens=1000) -> str:
      log.debug("Sending request to OpenAI...")
      
      headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"
      }
      
      payload = {
        "model": "gpt-4o",
        "response_format" : {"type" : "json_object"},
        "messages": [
          {
            "role": "user",
            "content": [
              {
                "type": "text",
                "text":
                  "Please review this submission for me."
                  "Please give me a response in the form of a JSON dictionary with the following keys:\n"
                  "possible points : the number of points possible from the problem\n"
                  "awarded points : how many points do you award to the student's submission\n"
                  "student text : what did the student write as their answer to the question\n"
                  "explanation : why are you assigning the grade you are\n"
              },
              {
                "type": "image_url",
                "image_url": {
                  "url": f"data:image/png;base64,{question.get_b64()}"
                }
              }
            ]
          }
        ],
        "max_tokens": max_tokens
      }
      
      response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
      response_str = response.json()["choices"][0]["message"]["content"]
      log.debug(f"restore_str: {response_str}")
      return json.loads(response_str)
      
      
  _id_counter = itertools.count()  # create an iterator that returns consecutive integers
  
  def __init__(self, input_pdf: str, question_locations: List[QuestionLocation], question_margin=10):
    self.id = next(self._id_counter)  # get the next unique id
    self.input_pdf = input_pdf
    self.pdf_doc = fitz.open(self.input_pdf)
    self.page_scores = {i: None for i in range(self.pdf_doc.page_count)}
    
    self.questions: List[Submission.Question] = []
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
          Submission.Question(q_start.question_number, PIL.Image.open(io.BytesIO(question_pixmap.tobytes())))
        )
        log.debug(f"stored q{self.questions[-1].number}")
      self.questions = sorted(self.questions, key=(lambda q: q.number))
      log.debug(f"num question: {len(self.questions)}")
  
  def __str__(self):
    return f"Submission_{self.id}({self.pdf_doc.page_count})"
  
  def get_page(self, page_number) -> fitz.Page:
    return self.pdf_doc[page_number]

  @classmethod
  def read_directory(cls, path_to_directory, base_exam, shuffle=True) -> List[Submission]:
    files = get_file_list(os.path.expanduser(path_to_directory))
    for f in files:
      if ".DS_Store" in f:
        os.remove(f)
        files.remove(f)
    
    question_locations = cls.get_question_locations(base_exam)
    submissions = [
      Submission(f, question_locations)
      for f in files
    ]
    
    if shuffle:
      random.shuffle(submissions)
    
    return submissions
    
  
  @staticmethod
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


