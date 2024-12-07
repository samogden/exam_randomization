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
      title = None,
      *,
      is_practice=False
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
      "quiz_type" : "assignment" if not is_practice else "practice_quiz",
      "description": """
        This quiz is aimed to help you practice skills.
        Please take it as many times as necessary to get full marks!
        Please note that although the answers section may be a bit lengthy,
        below them is often an in-depth explanation on solving the problem!
      """
    })
    return q

  def push_quiz_to_canvas(
      self,
      quiz: quiz.Quiz,
      num_variations: int,
      title: typing.Optional[str] = None,
      is_practice = False
  ):
    assignment_group = self.create_assignment_group()
    canvas_quiz = self.add_quiz(assignment_group, title, is_practice=is_practice)
    
    all_variations = set()
    for question_i, question in enumerate(quiz):
      log.debug(f"Generating #{question_i} ({question.name})")
  
      group : canvasapi.quiz.QuizGroup = canvas_quiz.create_question_group([
        {
          "name": f"{question.name}",
          "pick_count": 1,
          "question_points": question.points_value
        }
      ])
      
      # Track all variations across every question, in case we have duplicate questions
      variation_count = 0
      for attempt_number in range(QUESTION_VARIATIONS_TO_TRY):
        
        # Get the question in a format that is ready for canvas (e.g. json)
        question_for_canvas = question.get__canvas(self.course, canvas_quiz)
        question_fingerprint = question_for_canvas["question_text"]
        question_fingerprint += ''.join([a["answer_text"] for a in question_for_canvas["answers"]])
        
        # if it is in the variations that we have already seen then skip ahead, else track
        if question_fingerprint in all_variations:
          continue
        all_variations.add(question_fingerprint)
        
        # Set group ID to add it to the question group
        question_for_canvas["quiz_group_id"] = group.id
        
        # Push question to canvas
        log.debug(f"Pushing #{question_i} ({question.name}) {variation_count+1} / {num_variations} to canvas...")
        try:
          canvas_quiz.create_question(question=question_for_canvas)
        except canvasapi.exceptions.CanvasException as e:
          log.warning("Encountered Canvas error.")
          log.warning(e)
          log.warning("Sleeping for 1s...")
          time.sleep(1)
          continue
        
        # Update and check variations already seen
        variation_count += 1
        if variation_count >= num_variations:
          break
        if variation_count >= question.possible_variations:
          break
        

def main():
  pass

if __name__ == "__main__":
  main()
