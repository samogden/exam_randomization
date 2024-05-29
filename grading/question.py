#!env python
from __future__ import annotations

import abc
import base64
import io
import itertools
import json
import logging
import os
import random
from pprint import pprint
from typing import List, Dict

import PIL.Image
import pymupdf as fitz
import requests

import tkinter as tk
from tkinter import scrolledtext

from openai import OpenAI


# from assignment import QuestionLocation

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class Question:
  def __init__(self, question_number, responses : List[Response], max_points = 0):
    self.question_number = question_number
    self.responses : List[Response] = responses
    self.max_points = max_points
  
  def __str__(self):
    return f"Question({self.question_number}, {len(self.responses)})"
  
  
  def get_tkinter_frame(self, parent) -> tk.Frame:
    frame = tk.Frame(parent)
    
    # Make a scrollbar for the Listbox
    question_scrollbar = tk.Scrollbar(frame)
    question_scrollbar.pack(side=tk.RIGHT, fill=tk.BOTH)
    
    # Make a Listbox for questions
    question_listbox = tk.Listbox(frame, yscrollcommand=question_scrollbar.set)
    for i, r in enumerate(self.responses):
      question_listbox.insert(i, r)
    question_listbox.pack()
    question_listbox.focus()
    
    def doubleclick_callback(_):
      selected_response = self.responses[question_listbox.curselection()[0]]
      new_window = tk.Toplevel(parent)
      question_frame = selected_response.get_tkinter_frame(new_window)
      question_frame.pack()
      log.info(pprint(selected_response.get_chat_gpt_response()))
    
    # Set up a callback for double-clicking
    question_listbox.bind('<Double-1>', doubleclick_callback)
    
    frame.pack()
    return frame


class Response(abc.ABC):
  """
  Class for containing student responses to a question
  """
  def __init__(self, student_id):
    self.student_id = student_id
    
    # Things that we'll get from the user or from elsewhere
    self.score = None
    self.feedback = None
    self.score_gpt = None
    self.feedback_gpt = None
    
  def __str__(self):
    return f"Response({self.student_id}, {self.score})"
  
  @abc.abstractmethod
  def _get_response_for_gpt(self) -> Dict:
    pass
  
  def get_chat_gpt_response(self, system_prompt=None, examples=None, max_tokens=1000) -> str:
    log.debug("Sending request to OpenAI...")
    
    messages = []
    # Add system prompt, if applicable
    if system_prompt is not None:
      messages.append(
        {
          "role": "system",
          "content": [
            {
              "type": "text",
              "text": f"{system_prompt}"
            }
          ]
        }
      )
    
    # Add in examples for few-shot learning
    if examples is not None:
      messages.extend(examples)
    
    # Add grading criteria
    messages.append(
      {
        "role": "user",
        "content": [
          {
            "type": "text",
            "text":
              "Please review this submission for me."
              "Please give me a response in the form of a JSON dictionary with the following keys:\n"
              "possible points : the number of points possible from the problem\n"
              "awarded points : how many points do you award to the student's submission, and only use integer value\n"
              "student text : what did the student write as their answer to the question\n"
              "explanation : why are you assigning the grade you are\n"
          },
          self._get_response_for_gpt()
        ]
      }
    )
    
    client = OpenAI()
    response = client.chat.completions.create(
      model="gpt-4o",
      response_format={ "type": "json_object"},
      messages=messages,
      temperature=1,
      max_tokens=max_tokens,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    
    return json.loads(response.choices[0].message.content)

class Response_fromPDF(Response):
  def __init__(self, student_id, img: PIL.Image.Image):
    super().__init__(student_id)
    self.img : PIL.Image.Image = img
  
  @classmethod
  def load_from_pdf(cls, student_id, path_to_pdf, question_locations, question_margin=10) -> Dict[int,Response]:
    pdf_doc = fitz.open(path_to_pdf)
    responses: Dict[int,Response] = {}
    for (page_number, page) in enumerate(pdf_doc.pages()):
      
      # Find the size of the page so we can take a slice out of it
      page_width = page.rect.width
      page_height = page.rect.height
      
      # Filter out to only the questions that are on the current page
      questions_on_page = list(filter((lambda ql: ql.page_number == page_number), question_locations))
      
      # Walk through all the questions one and grab pictures out
      for (q_start, q_end) in zip(questions_on_page, questions_on_page[1:] + [None]):
        if q_end is None:
          question_rect = fitz.Rect(0, q_start.location - question_margin, page_width, page_height)
        else:
          question_rect = fitz.Rect(0, q_start.location, page_width - question_margin, q_end.location + question_margin)
        question_pixmap = page.get_pixmap(matrix=fitz.Matrix(1, 1), clip=question_rect)
        responses[q_start.question_number] = cls(
          student_id,
          PIL.Image.open(io.BytesIO(question_pixmap.tobytes()))
        )
      
    return responses
  
  def get_b64(self, format="PNG"):
    # Create a BytesIO buffer to hold the image data
    buffered = io.BytesIO()
    
    # Save the image to the buffer in the specified format
    self.img.save(buffered, format=format)
    
    # Get the byte data from the buffer
    img_byte = buffered.getvalue()
    
    # Encode the byte data to base64
    img_base64 = base64.b64encode(img_byte)
    
    # Convert the base64 byte data to a string
    img_base64_str = img_base64.decode('utf-8')
    
    return img_base64_str
  
  def _get_response_for_gpt(self):
    return {
      "type": "image_url",
      "image_url": {
        "url": f"data:image/png;base64,{self.get_b64()}"
      }
    }
  
  def get_tkinter_frame(self, parent) -> tk.Frame:
    frame = tk.Frame(parent)
    
    self.photo = PIL.ImageTk.PhotoImage(self.img)
    self.label = tk.Label(frame, image=self.photo, compound="top")
    self.label.grid(row=0, column=0)
    
    # Text area for GPT feedback
    # text_area = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=60, height=20)
    # text_area.grid(row=0, column=2)
    
    # Create a button
    # generate_gpt_button = ttk.Button(new_frame, text="Query GPT", command=(lambda :self.query_gpt(question, text_area)))
    # generate_gpt_button.grid(row=1, columnspan=True)
    
    # if hasattr(self, "question_frame"): self.question_frame.destroy()
    # self.question_frame = frame
    # self.question_frame.grid(row=0, column=0)
    
    return frame