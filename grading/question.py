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
  
  def get_chat_gpt_response(self, question : Question, max_tokens=1000) -> str:
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
  
  
