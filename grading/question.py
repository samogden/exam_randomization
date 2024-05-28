#!env python
from __future__ import annotations

import base64
import io
import itertools
import json
import logging
import os
import random
from typing import List, Dict

import PIL.Image
import pymupdf as fitz
import requests

import tkinter as tk
from tkinter import scrolledtext


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
  
  def get_chat_gpt_response(self, question : Question, max_tokens=1000) -> str:
    # todo: this will have to be moved so all of the questions can be checked with the same prompt so we can do few-shot learning
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
    
    # Set up a callback for double-clicking
    question_listbox.bind('<Double-1>', doubleclick_callback)
    
    frame.pack()
    return frame


class Response:
  """
  Class for containing student responses to a question
  """
  def __init__(self, student_id):
    self.student_id = student_id
    self.score = None
  
  def __str__(self):
    return f"Response({self.student_id}, {self.score})"

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
    self.image.save(buffered, format=format)
    
    # Get the byte data from the buffer
    img_byte = buffered.getvalue()
    
    # Encode the byte data to base64
    img_base64 = base64.b64encode(img_byte)
    
    # Convert the base64 byte data to a string
    img_base64_str = img_base64.decode('utf-8')
    
    return img_base64_str
  
  
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