#!env python
import itertools
import os.path
import pprint
import random

import question

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
    
    # Plan: right now we just take in questions and then assume they have a score and a "generate" button
  
  def describe(self):
    log.info(f"{self.exam_name} : {sum(map(lambda q: q.value, self.questions))}points : {len(self.questions)} / {len(self.possible_questions)} questions picked")
  
  def select_questions(self, total_points, exam_outline: List[Dict]):
    # The exam_outline object should contain a description of the kinds of questions that we want.
    # It will be a list of dictionaries that has "num questions" and then the appropriate filters.
    # We will walk through it and pick an appropriate set of questions, ensuring that we only select each once (unless we can pick more than once)
    # After we've gone through all the rules, we can backfill with whatever is left

    # todo: make this a set
    questions_picked = set()
    
    possible_questions = set(self.possible_questions)
    
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
    self.questions = questions_picked
    
  def generate(self, question_kind_sort_order=None, *args, **kwargs) -> List[str]:
    def sort_func(q):
      if question_kind_sort_order is not None:
        try:
          return (-q.value, question_kind_sort_order.index(q.kind))
        except ValueError:
          return (-q.value, float('inf'))
      return -q.value
    
    lines = []
    lines.extend(self.get_header(*args, **kwargs))
    lines.extend(["", ""])
    for question in sorted(self.questions, key=sort_func):
      lines.extend(question.generate(*args, **kwargs))
      lines.extend(["", ""])
    lines.extend(["", ""])
    lines.extend(self.get_footer(*args, **kwargs))
    
    return lines
  
  def get_header(self, *args, **kwargs) -> List[str]:
    if kwargs.get("to_latex", False):
      lines = [
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
        
        r"\setlist{itemsep=1.25em}",
      
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
      ]
      if len(self.instructions):
        lines.extend([
          "",
          r"\noindent\textbf{Instructions:}",
          r"\noindent " + self.instructions
        ])
      
      return lines
    return [
      f"{self.exam_name}",
      "Name:"
    ]
  
  def get_footer(self, *args, **kwargs) -> List[str]:
    if kwargs.get("to_latex", False):
      return [
        r"\end{document}"
      ]
    return []
  
  
  def get_extras__latex(self) -> List[str]:
    """Get the includes and anything else we need to have in addition to questions"""
    return []
  
  
  def get_latex(self) -> str:
    return '\n'.join(
      self.get_header__latex()
      + self.get_extras__latex()
      + self.get_questions__latex()
      + self.get_footer__latex()
    )
  
  
  
if __name__ == "__main__":
  questions = []
  questions.extend(question.Question_legacy.from_yaml(os.path.expanduser("~/repos/data/CST334/exam_questions/2024/exam2.8point.yaml")))
  questions.extend(question.Question_legacy.from_yaml(os.path.expanduser("~/repos/data/CST334/exam_questions/2024/exam2.4points.yaml")))
  questions.extend(question.Question_legacy.from_yaml(os.path.expanduser("~/repos/data/CST334/exam_questions/2024/exam2.2points.yaml")))
  questions.extend(question.Question_legacy.from_yaml(os.path.expanduser("~/repos/data/CST334/exam_questions/2024/exam2.1points.yaml")))
  
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
  quiz.select_questions(100,
    exam_outline=[
      {
        "num_to_pick" : 2,
        "filters" : {
          "kind" : question.Question.KIND.MEMORY,
          "value" : 8
        }
      },
      {
        "num_to_pick" : 2,
        "filters" : {
          "kind" : question.Question.KIND.PROCESS,
          "value" : 8
        }
      }
    ]
  )
  log.debug(quiz.questions)
  quiz.describe()
  
  print('\n'.join(
    quiz.generate(
      to_latex=True,
      question_kind_sort_order=[
        question.Question.KIND.MEMORY,
        question.Question.KIND.PROCESS
      ]
    )
  ))
  