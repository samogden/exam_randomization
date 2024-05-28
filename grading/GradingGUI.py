#! env python


import argparse
import base64
import itertools
import json
import logging
import os
import random
import threading
from typing import List
import io
import dotenv

import PIL.Image
import PIL.ImageTk as ImageTK

import tkinter as tk
import tkinter.ttk as ttk
from tkinter import scrolledtext as tk_scrolledtext

from assignment import Assignment, ScannedExam
from question import Question

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



class GradingGUI:
  def __init__(self, root, submissions: List[Assignment]|None):
    self.root = root
    self.root.title("Grading")
    
    if submissions is None:
      # todo: get submissions
      pass
    else:
      self.submissions : List[Assignment] = submissions
    
    self.curr_question_number = 0
    
    self.curr_question: Assignment.Question = self.submissions[0].questions[self.curr_question_number]
    
    self.create_widgets()
  
  def next_submission(self):
    # We basically keep the same question number and then pick a random submission that hasn't had that question answered yet
    log.debug(f"self.submissions: {[str(s.questions[self.curr_question_number]) for s in self.submissions]}")
    possible_next_submissions = list(filter(
      lambda s : s.questions[self.curr_question_number].grade is None,
      self.submissions
    ))
    if len(possible_next_submissions) == 0:
      log.info("All done!")
      return
    next_submission = random.choice(possible_next_submissions)
    log.debug(f"Moving on to submission {next_submission}")
    
    self.curr_question = next_submission.questions[self.curr_question_number]
    self.update_question_frame(self.curr_question)
  
  
  def create_widgets(self):
    
    self.update_question_frame(self.curr_question)
    self.question_frame.grid(row=0, column=0)
    
    # Create an entry widget
    self.score_entry = ttk.Entry(self.root)
    # self.score_entry.pack(pady=10)
    self.score_entry.grid(row=1, column=0)
    
    self.submit_button = ttk.Button(self.root, text="Submit", command=self.submit_score)
    # self.submit_button.pack(pady=10)
    self.submit_button.grid(row=2, column=0)
  
  def query_gpt(self, question, text_area):
    def replace_text_area(new_text):
      text_area.delete('1.0', tk.END)
      text_area.insert(tk.END, new_text)
    
    def query():
      gpt_response = question.get_chat_gpt_response(question)
      replace_text_area(gpt_response)
    
    replace_text_area("Querying OpenAI....")
    threading.Thread(target=query).start()
  
  def submit_score(self):
    score = self.score_entry.get()
    self.curr_question.grade = int(score)
    self.next_submission()
  
  def update_question_frame(self, question : Question) -> None:
    new_frame = ttk.Frame(self.root)
    
    self.photo = PIL.ImageTk.PhotoImage(question.image)
    self.label = ttk.Label(new_frame, image=self.photo, compound="top")
    self.label.grid(row=0, column=0)
    
    # Text area for GPT feedback
    text_area = tk_scrolledtext.ScrolledText(new_frame, wrap=tk.WORD, width=60, height=20)
    text_area.grid(row=0, column=2)
    
    # Create a button
    generate_gpt_button = ttk.Button(new_frame, text="Query GPT", command=(lambda :self.query_gpt(question, text_area)))
    generate_gpt_button.grid(row=1, columnspan=True)
    
    if hasattr(self, "question_frame"): self.question_frame.destroy()
    self.question_frame = new_frame
    self.question_frame.grid(row=0, column=0)

def main():
  flags = parse_flags()
  dotenv.load_dotenv()
  
  a = ScannedExam(flags.base_exam, flags.input_dir)
  print(a)
  
  return
  
  
  submissions = Assignment.read_directory(flags.input_dir, flags.base_exam)
  
  root = tk.Tk()
  app = GradingGUI(root, submissions)
  root.mainloop()


if __name__ == "__main__":
  main()