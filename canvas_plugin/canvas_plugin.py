#!env python
import pprint
import time

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


def add_question(
    canvas : canvasapi.Canvas,
    course: canvasapi.course.Course,
    quiz: canvasapi.quiz.Quiz,
    question: question_module.CanvasQuestion
):
  
  question_text = '<br>\n'.join(question.get_question_body())
  answers = []
  for blank_name, var in question.blank_vars.items():
    log.debug(f"var: {pprint.pformat(var.__dict__)}")
    for variation in var.get_answers():
      answers.append({
        "blank_id": blank_name,
        "answer_text": variation,
        "answer_weight": 100
      })
  
  q = quiz.create_question(
    question={
      "question_name": f"question created at {time.time()}",
      "question_text": f"{question_text}",
      # "quiz_group_id": #todo
      "question_type": "fill_in_multiple_blanks_question",
      # "question_type": "true_false_question",
      "points_possible": 1,
      "answers": answers
    }
  )

def main():
  dotenv.load_dotenv()
  canvas = canvasapi.Canvas(os.environ.get("CANVAS_API_URL"), os.environ.get("CANVAS_API_KEY"))
  course = canvas.get_course(23751)
  quiz = course.get_quiz(98873)
  
  question = memory_questions.Paging_canvas()
  add_question(canvas, course, quiz, question)
  

if __name__ == "__main__":
  main()