#!env python
import pprint
import time
from typing import Dict

import canvasapi
import canvasapi.course
import canvasapi.quiz
import dotenv, os


from question_generator import question as question_module
from question_generator import memory_questions as memory_questions

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def get_question_for_canvas(question: question_module.CanvasQuestion) -> Dict:
  
  question_text = '<br>\n'.join(question.get_question_body())
  answers = []
  for blank_name, var in question.blank_vars.items():
    log.debug(f"var: {pprint.pformat(var.__dict__)}")
    for variation in var.get_answers():
      answers.append({
        "blank_id": blank_name,
        "answer_text": variation,
        "answer_weight": 100,
      })
  return {
    "question_name": f"question created at {time.time()}",
    "question_text": f"{question_text}",
    # "quiz_group_id": #todo
    "question_type": "fill_in_multiple_blanks_question",
    # "question_type": "true_false_question",
    "points_possible": 1,
    "answers": answers,
    # todo: "neutral_comments" are per-answer, so we should make them more specific
    "neutral_comments_html": '<br>\n'.join(question.get_explanation())
  }
  
  

def add_question(
    canvas : canvasapi.Canvas,
    course: canvasapi.course.Course,
    quiz: canvasapi.quiz.Quiz,
    question: question_module.CanvasQuestion
):
  
  q = quiz.create_question(
    question=get_question_for_canvas(question)
  )


def add_question_group(
    canvas : canvasapi.Canvas,
    course: canvasapi.course.Course,
    quiz: canvasapi.quiz.Quiz,
    num_to_add: int
):
  group = quiz.create_question_group([
    {
      "name": "Paging Questions",
      "pick_count": 5,
      "question_points": 1
    }
  ])
  questions_to_add = set()
  while len(questions_to_add) < num_to_add:
    log.debug(f"Currently have {len(questions_to_add)}")
    questions_to_add.add(memory_questions.Paging_canvas())
    
  for q in questions_to_add:
    question_for_canvas = get_question_for_canvas(q)
    question_for_canvas["quiz_group_id"] = group.id
    quiz.create_question(question=question_for_canvas)

def add_quiz(
    canvas : canvasapi.Canvas,
    course: canvasapi.course.Course,
    num_questions: int
):
  q = course.create_quiz(quiz={
    "title": f"New Quiz {time.time()}",
    "hide_results" : None,
    "show_correct_answers": True,
    "scoring_policy": "keep_highest",
    "allowed_attempts": -1,
  })
  return q

def main():
  dotenv.load_dotenv()
  canvas = canvasapi.Canvas(os.environ.get("CANVAS_API_URL"), os.environ.get("CANVAS_API_KEY"))
  course = canvas.get_course(25068)
  quiz = course.get_quiz(98876)
  # quiz = add_quiz(canvas, course, 10)
  
  add_question(canvas, course, quiz, memory_questions.Paging_canvas())
  # add_question_group(canvas, course, quiz, 10)
  
  for q in quiz.get_questions():
    log.debug(f"{pprint.pformat(q.__dict__)}")
  

if __name__ == "__main__":
  main()