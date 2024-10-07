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

sys.path.append(os.getcwd())
print(sys.path)

from question_generator import question as question_module
from question_generator import memory_questions as memory_questions
from question_generator import math_questions as math_questions
from question_generator import process_questions as process_questions

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

QUESTION_GENERATOR_ATTEMPT_TIMEOUT_MULTIPLIER = 10


def get_question_for_canvas(
    course: canvasapi.course.Course,
    quiz: canvasapi.quiz.Quiz,
    question: question_module.CanvasQuestion,
) -> Dict:
  
  question_text = '<br>\n'.join(question.get_question_body())
  answers = []
  for blank_name, var in question.blank_vars.items():
    for variation in var.get_answers():
      answers.append({
        "blank_id": blank_name,
        "answer_text": variation,
        "answer_weight": 100,
      })
  log.debug(f"question.img: {question.img}")
  return {
    "question_name": f"question created at {datetime.now().strftime('%m/%d/%y %H:%M:%S.%f')}",
    "question_text": f"{question_text}",
    "question_type": "fill_in_multiple_blanks_question",
    "points_possible": 1,
    "answers": answers,
    "neutral_comments_html": '<br>\n'.join(question.get_explanation(course, quiz))
  }
  

def add_question_group(
    canvas : canvasapi.Canvas,
    course: canvasapi.course.Course,
    quiz: canvasapi.quiz.Quiz,
    num_to_add: int,
    existing_questions: Set[question_module.Question],
    question_class : question_module.CanvasQuestion,
):
  group = quiz.create_question_group([
    {
      "name": "Paging Questions",
      "pick_count": 1,
      "question_points": 1
    }
  ])
  
  questions_to_add = set()
  counter = 0
  while (len(questions_to_add) < num_to_add) and (counter < num_to_add * QUESTION_GENERATOR_ATTEMPT_TIMEOUT_MULTIPLIER):
    counter += 1
    log.debug(f"Currently have {len(questions_to_add)}")
    new_question = question_class()
    if new_question in existing_questions:
      continue
    questions_to_add.add(new_question)
    
  for q in questions_to_add:
    question_for_canvas = get_question_for_canvas(course, quiz, q)
    question_for_canvas["quiz_group_id"] = group.id
    quiz.create_question(question=question_for_canvas)
  
  return questions_to_add

def add_quiz(
    canvas : canvasapi.Canvas,
    course: canvasapi.course.Course,
    assignment_group: canvasapi.course.AssignmentGroup|None = None
):
  q = course.create_quiz(quiz={
    "title": f"New Quiz {datetime.now().strftime('%m/%d/%y %H:%M:%S.%f')}",
    "hide_results" : None,
    "show_correct_answers": True,
    "scoring_policy": "keep_highest",
    "allowed_attempts": -1,
    "assignment_group_id": assignment_group.id,
    "description": """
      This quiz is aimed to help you practice skills.
      Please take it as many times as necessary to get full marks!
      Please note that although the answers section may be a bit lengthy, check below them for a full explanation of how to solve the problem!
    """
  })
  return q

def create_quiz_with_questions(
    canvas: canvasapi.Canvas,
    course: canvasapi.course.Course,
    question_classes : question_module.CanvasQuestion|typing.List[question_module.CanvasQuestion],
    assignment_group: canvasapi.course.AssignmentGroup|None = None,
    num_groups = 5,
    questions_per_group = 10
):
  quiz = add_quiz(canvas, course, assignment_group)
  
  if not isinstance(question_classes, collections.abc.Iterable):
    question_classes = [question_classes]
  
  quiz_questions = set()
  for i in range(num_groups):
    quiz_questions.union(
      add_question_group(
        canvas,
        course,
        quiz,
        questions_per_group,
        quiz_questions,
        question_classes[i%len(question_classes)]
      )
    )
    
  
  # for q in quiz.get_questions():
  #   log.debug(f"{pprint.pformat(q.__dict__)}")

def create_assignment_group(canvas: canvasapi.Canvas, course: canvasapi.course.Course, name="dev") -> canvasapi.course.AssignmentGroup:
  for assignment_group in course.get_assignment_groups():
    if assignment_group.name == name:
      log.info("Found group existing, returning")
      return assignment_group
  assignment_group = course.create_assignment_group(
    name="dev",
    group_weight=0.0,
    position=0,
  )
  return assignment_group

def test(course, *args, **kwargs):
  pass

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
  
  if args.test:
    return test(course=canvas.get_course(args.course_id))
  
  course = canvas.get_course(args.course_id)
  assignment_group = create_assignment_group(canvas, course)
  create_quiz_with_questions(
    canvas,
    course,
    question_classes=[
      math_questions.BitsAndBytes,
      math_questions.HexAndBinary
    ],
    # process_questions.SchedulingQuestion_canvas,
    assignment_group=assignment_group,
    num_groups=args.num_groups,
    questions_per_group=args.questions_per_group,
  )
  

if __name__ == "__main__":
  main()