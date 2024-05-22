#!env python

import argparse
import base64
import itertools
import logging
import os
import random
from typing import List
import io
import dotenv

import PIL.Image
import PIL.ImageTk as ImageTK
import tkinter as tk
import tkinter.ttk as ttk

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
    
  _id_counter = itertools.count()  # create an iterator that returns consecutive integers
  
  def __init__(self, input_pdf: str, question_locations: List[QuestionLocation], question_margin=10):
    self.id = next(self._id_counter)  # get the next unique id
    self.input_pdf = input_pdf
    self.pdf_doc = fitz.open(self.input_pdf)
    self.page_scores = {i: None for i in range(self.pdf_doc.page_count)}
    
    self.questions : List[Submission.Question] = []
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



def get_chat_gpt_response(base64_png) -> str:
  log.debug("Sending request to OpenAI...")
  
  return "here's a string!"
  
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
            "text":
              "Please review this submission for me.  Please give me response in the form of a JSON dictionary with the following keys:\n"
              "possible points : the number of points possible from the problem\n"
              "awarded points : how many points do you award to the student's submission\n"
              "student text : what did the student write as their answer to the question\n"
              "explanation : why are you assigning the grade you are\n"
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
  response_str = response.json()["choices"][0]["message"]["content"]
  log.debug(f"restore_str: {response_str}")
  return response_str


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



class MyApp:
  def __init__(self, root, submissions: List[Submission]):
    self.root = root
    self.root.title("Grading")
    
    self.submissions = submissions
    
    self.create_widgets()
  
  def create_widgets(self):
    
    first_question = self.submissions[0].questions[0]
    self.photo = PIL.ImageTk.PhotoImage(first_question.image)
  
    # Create a label with text and image
    self.label = ttk.Label(self.root, text="Hello, Tkinter!", image=self.photo, compound="top")
    self.label.pack(pady=10)
  
    # Create an entry widget
    self.entry = ttk.Entry(self.root)
    self.entry.pack(pady=10)
    
    # Create a button
    self.button = ttk.Button(self.root, text="Click Me", command=self.on_button_click)
    self.button.pack(pady=10)
  
  def on_button_click(self):
    # Handle the button click event
    entered_text = self.entry.get()
    self.label.config(text=f"Hello, {entered_text}!")


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
    
    
  question_locations = get_question_locations(flags.base_exam)
  submissions = [
    Submission(f, question_locations)
    for f in sorted(files, key=lambda _: random.random())[:2]
  ]
  
  root = tk.Tk()
  app = MyApp(root, submissions)
  root.mainloop()
  
  return
  
  root = tk.Tk()
  root.geometry('1000x1000')
  
  
  GradingGUI(root, submissions) #.pack() #.pack(side="top", fill="both", expand=True)
  
  root.mainloop()
  root.destroy()
  
  return
  
  if flags.debug:
    question_locations = get_question_locations(flags.base_exam)
    submissions = [
      Submission(f, question_locations)
      for f in sorted(files, key=lambda _: random.random())[:2]
    ]
    for question_number in range(0, len(submissions[0].questions)):  # todo: is there a more elegant way?
      grade_question(submissions, question_number)
      # log.info(f"Now grading Q{question_number} / {len(submissions[0].questions)}")
      # for submission in submissions:
      #   q = submission.questions[question_number]
      #   # q.present_question()
    
    # show_gui(submission.pdf_doc[0])
    
    # show_gui(page)
    return
  
  # for page_number in sorted(range(submissions[0].pdf_doc.page_count), key=(lambda _: random.random())):
  #   do_grading_pass(submissions, page_number, flags.query_ai, flags)
  #   break
  #
  # for submission in submissions:
  #   log.info(f"{submission} : {sum(filter(lambda v: v is not None, submission.page_scores.values()))}")


if __name__ == "__main__":
  main()
