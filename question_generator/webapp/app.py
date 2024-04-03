#!env python
import random

import flask
from flask import request

import process_questions, memory_questions


import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

app = flask.Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def root():
  
  if request.method == 'GET':
    q = process_questions.SchedulerQuestion_FIFO(num_jobs=2, max_arrival_time=1, max_duration=5)
    return flask.render_template(
      "question.html",
      question_prelude = q.get_question_prelude(),
      given_vars = [str(q) for q in q.given_vars],
      target_vars = [q.get_info() for q in q.target_vars]
    )
  elif request.method == "POST":
    results = []
    for name, given_answer in request.form.items():
      if name.endswith("-answer"): continue
      
      results.append(
        (
          name,
          given_answer,
          request.form.get(f'{name}-answer')
        )
      )
      
    def compare_result(name, given_answer, true_answer):
      if given_answer == true_answer:
        return f"<b>{name}:</b> correct!"
      else:
        return f"<b>{name}: incorrect!</b> {given_answer} != {true_answer}"
      
    return flask.render_template(
      "results.html",
      results=results
    )
    
    return f"got a post!"



@app.route("/<question_type>", methods=['GET', 'POST'])
def question(question_type):
  if request.method == 'GET':
    if question_type == "memory":
      questions = [
        # math_questions.BitsAndBytes,
        memory_questions.VirtualAddress_parts,
        memory_questions.BaseAndBounds,
        memory_questions.Paging
      ]
    elif question_type == "scheduler":
      
      questions = [
        process_questions.SchedulerQuestion_FIFO,
        process_questions.SchedulerQuestion_ShortestTimeRemaining,
        process_questions.SchedulerQuestion_ShortestDuration,
        process_questions.SchedulerQuestion_Roundrobin
      ]
    else:
      questions = [
        memory_questions.BitsAndBytes,
        memory_questions.VirtualAddress_parts,
        process_questions.SchedulerQuestion_FIFO,
        process_questions.SchedulerQuestion_ShortestTimeRemaining,
        process_questions.SchedulerQuestion_ShortestDuration,
        process_questions.SchedulerQuestion_Roundrobin
      ]
    q = random.choice(questions)()
    return flask.render_template(
      "question.html",
      question_prelude = q.get_question_prelude(),
      given_vars = [str(q) for q in q.given_vars],
      target_vars = [q.get_info() for q in q.target_vars]
    )
  elif request.method == "POST":
    results = []
    for name, given_answer in request.form.items():
      if name.endswith("-answer"): continue
      
      results.append(
        (
          name,
          given_answer,
          request.form.get(f'{name}-answer')
        )
      )
    
    def compare_result(name, given_answer, true_answer):
      if given_answer == true_answer:
        return f"<b>{name}:</b> correct!"
      else:
        return f"<b>{name}: incorrect!</b> {given_answer} != {true_answer}"
    
    return flask.render_template(
      "results.html",
      results=results
    )
    
    return f"got a post!"


if __name__ == '__main__':
  app.run(debug=True, port=80)