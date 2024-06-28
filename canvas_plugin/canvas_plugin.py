#!env python
import pprint
import time

import canvasapi
import canvasapi.course
import canvasapi.quiz
import dotenv, os

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def add_question(canvas : canvasapi.Canvas, course: canvasapi.course.Course, quiz: canvasapi.quiz.Quiz):
  q = quiz.create_question(
    question={
      "question_name": f"question created at {time.time()}",
      "question_text": f"The first answer is [this], and the other is [that]",
      # "quiz_group_id": #todo
      "question_type": "fill_in_multiple_blanks_question",
      # "question_type": "true_false_question",
      "points_possible": 1,
      "answers": [
        {
          "blank_id": "this",
          "answer_text": "thing1",
          "answer_weight": 100
        },
        {
          "blank_id": "that",
          "answer_text": "thing2",
          "answer_weight": 100
        }
      ]
    }
  )

def main():
  dotenv.load_dotenv()
  canvas = canvasapi.Canvas(os.environ.get("CANVAS_API_URL"), os.environ.get("CANVAS_API_KEY"))
  course = canvas.get_course(23751)
  quiz = course.get_quiz(98873)
  
  add_question(canvas, course, quiz)
  
  

if __name__ == "__main__":
  main()