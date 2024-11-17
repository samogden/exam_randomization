#!env python

import argparse
import collections.abc
import pprint
import time
import typing
from datetime import datetime
from typing import Dict, Set

import canvasapi
import canvasapi.course
import canvasapi.quiz
import dotenv, os
import sys

import question
import quiz

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


logger = logging.getLogger("canvasapi")
handler = logging.StreamHandler(sys.stderr)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

handler.setLevel(logging.WARNING)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)


QUESTION_VARIATIONS_TO_TRY = 1000


class CanvasInterface:
  def __init__(self, *, course_id : int, prod=False):
    super().__init__()
    dotenv.load_dotenv(os.path.join(os.path.expanduser("~"), ".env"))
    log.debug(os.environ.get("CANVAS_API_URL"))
    if prod:
      log.warning("Using canvas PROD!")
      self.canvas = canvasapi.Canvas(os.environ.get("CANVAS_API_URL_prod"), os.environ.get("CANVAS_API_KEY_prod"))
    else:
      log.info("Using canvas DEV")
      self.canvas = canvasapi.Canvas(os.environ.get("CANVAS_API_URL"), os.environ.get("CANVAS_API_KEY_prod"))
    self.course = self.canvas.get_course(course=course_id)
  
  def create_assignment_group(self, name="dev") -> canvasapi.course.AssignmentGroup:
    for assignment_group in self.course.get_assignment_groups():
      if assignment_group.name == name:
        log.info("Found group existing, returning")
        return assignment_group
    assignment_group = self.course.create_assignment_group(
      name="dev",
      group_weight=0.0,
      position=1,
    )
    return assignment_group
  
  def add_quiz(
      self,
      assignment_group: canvasapi.course.AssignmentGroup,
      title = None
  ):
    if title is None:
      title = f"New Quiz {datetime.now().strftime('%m/%d/%y %H:%M:%S.%f')}"
    
    q = self.course.create_quiz(quiz={
      "title": title,
      "hide_results" : None,
      "show_correct_answers": True,
      "scoring_policy": "keep_highest",
      "allowed_attempts": -1,
      "shuffle_answers": True,
      "assignment_group_id": assignment_group.id,
      "description": """
        This quiz is aimed to help you practice skills.
        Please take it as many times as necessary to get full marks!
        Please note that although the answers section may be a bit lengthy,
        below them is often an in-depth explanation on solving the problem!
      """
    })
    return q

  def push_quiz_to_canvas(self, quiz: quiz.Quiz, num_variations: int):
    assignment_group = self.create_assignment_group()
    canvas_quiz = self.add_quiz(assignment_group)
    
    all_variations = set()
    for question in quiz:
  
      group : canvasapi.quiz.QuizGroup = canvas_quiz.create_question_group([
        {
          "name": f"{question.name}",
          "pick_count": 1,
          "question_points": 1
        }
      ])
      
      # Track all variations across every question, in case we have duplicate questions
      variation_count = 0
      for attempt_number in range(QUESTION_VARIATIONS_TO_TRY):
        
        # Get the question in a format that is ready for canvas (e.g. json)
        question_for_canvas = question.get_question_for_canvas(self.course, canvas_quiz)
        
        # if it is in the variations that we have already seen then skip ahead, else track
        if question_for_canvas["question_text"] in all_variations:
          continue
        all_variations.add(question_for_canvas["question_text"])
        
        # Set group ID to add it to the question group
        question_for_canvas["quiz_group_id"] = group.id
        
        # Push question to canvas
        log.debug(f"Pushing {question.name} {variation_count+1} / {num_variations} to canvas...")
        canvas_quiz.create_question(question=question_for_canvas)
        
        # Update and check variations already seen
        variation_count += 1
        if variation_count >= num_variations:
          break
        





def main():
  
  dotenv.load_dotenv()
  
  parser = argparse.ArgumentParser()
  parser.add_argument("--course_id", type=int, default=25523)
  parser.add_argument("--prod", action="store_true")
  parser.add_argument("--test", action="store_true")
  
  parser.add_argument("--num_groups", type=int, default=5)
  parser.add_argument("--questions_per_group", type=int, default=100)
  
  args = parser.parse_args()
  
  if args.prod:
    canvas = canvasapi.Canvas(os.environ.get("CANVAS_API_URL_prod"), os.environ.get("CANVAS_API_KEY_prod"))
  else:
    canvas = canvasapi.Canvas(os.environ.get("CANVAS_API_URL"), os.environ.get("CANVAS_API_KEY"))
  
  course = canvas.get_course(args.course_id)
  assignment_group = create_assignment_group(canvas, course)
  create_quiz_with_questions(
    canvas,
    course,
    question_classes=[
      # math_questions.BitsAndBytes,
    ],
    # process_questions.SchedulingQuestion_canvas,
    assignment_group=assignment_group,
    num_groups=args.num_groups,
    questions_per_group=args.questions_per_group,
  )

if __name__ == "__main__":
  main()
