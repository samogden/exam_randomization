#!env python
import collections
import enum
import itertools
import os.path
import pprint
import random
import shutil
import subprocess
import tempfile

import pypandoc

import question
import canvas_interface
from premade_questions import math_questions
from misc import OutputFormat

from typing import List, Dict

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


  
class Quiz:
  """
  A quiz object that will build up questions and output them in a range of formats (hopefully)
  It should be that a single quiz object can contain multiples -- essentially it builds up from the questions and then can generate a variety of questions.
  """
  
  def __init__(self, exam_name, possible_questions: List[dict|question.Question], *args, **kwargs):
    self.exam_name = exam_name
    self.possible_questions = possible_questions
    self.questions : List[question.Question] = []
    self.instructions = kwargs.get("instructions", "")
    self.question_sort_order = None
    
    # Plan: right now we just take in questions and then assume they have a score and a "generate" button
  
  def __iter__(self):
    def sort_func(q):
      if self.question_sort_order is not None:
        try:
          return (-q.value, self.question_sort_order.index(q.kind))
        except ValueError:
          return (-q.value, float('inf'))
      return -q.value
    return iter(sorted(self.questions, key=sort_func))
    
  
  def describe(self):
    counter = collections.Counter([q.value for q in self.questions])
    log.info(f"{self.exam_name} : {sum(map(lambda q: q.value, self.questions))}points : {len(self.questions)} / {len(self.possible_questions)} questions picked.  {list(counter.items())}")
    
  
  def select_questions(self, total_points=None, exam_outline: List[Dict]=None):
    # The exam_outline object should contain a description of the kinds of questions that we want.
    # It will be a list of dictionaries that has "num questions" and then the appropriate filters.
    # We will walk through it and pick an appropriate set of questions, ensuring that we only select each once (unless we can pick more than once)
    # After we've gone through all the rules, we can backfill with whatever is left

    if total_points is None:
      self.questions = self.possible_questions
      return
    
    questions_picked = set()
    
    possible_questions = set(self.possible_questions)
    
    if exam_outline is not None:
      for requirements in exam_outline:
        # Filter out to only get appropriate questions
        appropriate_questions = list(filter(
          lambda q: all([getattr(q, attr_name) == attr_val for (attr_name, attr_val) in requirements["filters"].items()]),
          possible_questions
        ))
        
        # Pick the appropriate number of questions
        questions_picked.update(
          random.sample(appropriate_questions, requirements["num_to_pick"])
        )
        
        # Remove any questions that were just picked so we don't pick them again
        possible_questions = set(possible_questions).difference(set(questions_picked))
        
    log.debug(f"Selected due to filters: {len(questions_picked)} ({sum(map(lambda q: q.value, questions_picked))}points)")
    
    if total_points is not None:
      # Figure out how many points we have left to select
      num_points_left = total_points - sum(map(lambda q: q.value, questions_picked))
      
      
      # To pick the remaining points, we want to take our remaining questions and select a subset that adds up to the required number of points
  
      # Find all combinations of objects that match the target value
      matching_sets = []
      for r in range(1, len(possible_questions) + 1):
        for combo in itertools.combinations(possible_questions, r):
          if sum(q.value for q in combo) == num_points_left:
            matching_sets.append(combo)
      
      # Pick a random matching set
      if matching_sets:
        random_set = random.choice(matching_sets)
      else:
        log.error("Cannot find any matching sets")
    
      questions_picked.update(random_set)
    else:
      # todo: I know this snippet is repeated.  Oh well.
      questions_picked = self.possible_questions
    self.questions = questions_picked
  
  def get_latex(self) -> str:
    text = self.get_header(OutputFormat.LATEX) + "\n\n"
    for question in self:
      text += question.get__latex() + "\n\n"
    text += self.get_footer(OutputFormat.LATEX)
    return text
  
  
  def get_header(self, output_format: OutputFormat, *args, **kwargs) -> str:
    lines = []
    if output_format == OutputFormat.LATEX:
      lines.extend([
        r"\documentclass{article}",
        r"\usepackage[a4paper, margin=1in]{geometry}",
        r"\usepackage{times}",
        r"\usepackage{tcolorbox}",
        r"\usepackage{graphicx} % Required for inserting images",
        r"\usepackage{booktabs}",
        r"\usepackage[final]{listings}",
        r"\usepackage[nounderscore]{syntax}",
        r"\usepackage{caption}",
        r"\usepackage{booktabs}",
        r"\usepackage{multicol}",
        r"\usepackage{subcaption}",
        r"\usepackage{enumitem}",
        
        # r"\setlist{itemsep=1.25em}",
      
        r"\newcounter{NumQuestions}",
        r"\newcommand{\question}[1]{ %",
        r"  \vspace{0.5cm}",
        r"  \stepcounter{NumQuestions} %",
        r"  \noindent\textbf{Question \theNumQuestions:} \hfill \rule{0.5cm}{0.15mm} / #1",
        r"  \par",
        r"  \vspace{0.1cm}",
        r"}",
        
        r"\newcommand{\answerblank}[1]{\rule[-1.5mm]{#1cm}{0.15mm}}",
        
        r"\title{" + self.exam_name + r"}",
        
        r"\begin{document}",
        r"\noindent\Large " + self.exam_name + r"\hfill \normalsize Name: \answerblank{5}",
        r"\vspace{0.5cm}"
      ])
      if len(self.instructions):
        lines.extend([
          "",
          r"\noindent\textbf{Instructions:}",
          r"\noindent " + self.instructions
        ])
    else:
      lines.extend([
        f"{self.exam_name}",
        "Name:"
      ])
    return '\n'.join(lines)
  
  def get_footer(self, output_format: OutputFormat, *args, **kwargs) -> str:
    lines = []
    if output_format == OutputFormat.LATEX:
      lines.extend([
        r"\end{document}"
      ])
    return '\n'.join(lines)
  
  def set_sort_order(self, sort_order):
    self.question_sort_order = sort_order


def generate_latex(q: Quiz):
  
  shutil.rmtree('out')
  
  tmp_tex = tempfile.NamedTemporaryFile('w')
  
  # tmp_tex.write(pypandoc.convert_text('\n'.join(q.get_lines(output_format=OutputFormat.LATEX)), 'latex', format='md'))
  tmp_tex.write(q.get_latex())
  tmp_tex.flush()
  shutil.copy(f"{tmp_tex.name}", "debug.tex")
  p = subprocess.Popen(
    f"latexmk -pdf -output-directory={os.path.join(os.getcwd(), 'out')} {tmp_tex.name}",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE)
  try:
    p.wait(30)
  except subprocess.TimeoutExpired:
    logging.error("Latex Compile timed out")
    p.kill()
    tmp_tex.close()
    return
  proc = subprocess.Popen(
    f"latexmk -c {tmp_tex.name} -output-directory={os.path.join(os.getcwd(), 'out')}",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
  )
  proc.wait(timeout=30)
  tmp_tex.close()
  
  
if __name__ == "__main__":
  questions = []
  
  # questions.extend(question.Question_legacy.from_yaml(os.path.expanduser("~/repos/data/CST334/exam_questions/2024/concurrency.yaml")))
  # questions.extend(question.Question_legacy.from_yaml(os.path.expanduser("~/repos/data/CST334/exam_questions/2024/memory.yaml")))
  # questions.extend(question.Question_legacy.from_yaml(os.path.expanduser("~/repos/data/CST334/exam_questions/2024/misc.yaml")))
  # questions.extend(question.Question_legacy.from_yaml(os.path.expanduser("~/repos/data/CST334/exam_questions/2024/persistance.yaml")))
  # questions.extend(question.Question_legacy.from_yaml(os.path.expanduser("~/repos/data/CST334/exam_questions/2024/processes.yaml")))
  # questions.append(
  #   math_questions.AverageMemoryAccessTime
  # )
  
  questions = [
    math_questions.BitsAndBytes()
  ]
  
  log.debug(f"Num questions available: {len(questions)}.  Total value: {sum(map(lambda q: q.value, questions))}")
  
  quiz = Quiz(
    "CST334 Exam 1",
    questions,
    instructions="""
      You have 110 minutes to complete this exam.
      Questions are arranged in order of decreasing value.
      Please fill out questions by circling the appropriate answer, or using the space provided.
      No devices besides calculators are allowed to be used during the exam.
    """
  )
  quiz.select_questions(None,
    exam_outline=[
      # {
      #   "num_to_pick" : 2,
      #   "filters" : {
      #     "kind" : question.Question.KIND.MEMORY,
      #     "value" : 8
      #   }
      # },
    ]
  )
  log.debug(quiz.questions)
  quiz.describe()
  
  quiz.set_sort_order([
    question.Question.TOPIC.MEMORY,
    question.Question.TOPIC.PROCESS
  ])
  #
  for _ in range(1):
    generate_latex(quiz)
  
  interface = canvas_interface.CanvasInterface(prod=False, course_id=25523)
  interface.push_quiz_to_canvas(quiz, 2)
  
  quiz.describe()