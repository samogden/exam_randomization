#!env python
import collections
import logging
import os
import shutil
import tempfile
from typing import Tuple, List

import jinja2
import pypdf
import question
import argparse
import subprocess

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("--num_exams", default=1, type=int)
  parser.add_argument("--questions_file", nargs='+')
  parser.add_argument("--debug", action="store_true")
  parser.add_argument("--exam_name", default="CST334 Exam 3")
  return parser.parse_args()


def generate_exam(questions_file, exam_name) -> Tuple[str, List[question]]:
  env = jinja2.Environment(
    loader=jinja2.FileSystemLoader("templates"),
    block_start_string='<BLOCK>',
    block_end_string='</BLOCK>',
    variable_start_string='<VAR>',
    variable_end_string='</VAR>',
    comment_start_string='<COMMENT>',
    comment_end_string='</COMMENT>',
  )
  question_set = question.QuestionSet(questions_file).questions
  question_set = sorted(
    question_set,
    key=lambda q: (-q.value, ["languages", "memory", "processes", "grabbag"].index(q.subject))
  )
  # return question_set
  
  def make_questions(*args, **kwargs):
    ## In this function we'll make the questions for the exam
    questions = [q.generate_latex(is_first=(i==0)) for i, q in enumerate(question_set)]
    
    return '\n\n'.join(questions)
  
  env.globals["generate_exam"] = make_questions
  env.globals["get_exam_name"] = (lambda : f"{exam_name}")
  template = env.get_template('exam_base.j2')
  
  rendered_output = template.render()
  return rendered_output, question_set


def main():
  args = parse_args()
  
  if os.path.exists("out"): shutil.rmtree("out")
  os.mkdir("out")
  
  for _ in range(args.num_exams):
    exam_text, question_set = generate_exam(questions_file=args.questions_file, exam_name=args.exam_name)
    if args.debug:
      tmp_tex = open("exam.tex", 'w')
    else:
      tmp_tex = tempfile.NamedTemporaryFile('w')
      
    tmp_tex.write(exam_text)
    tmp_tex.flush()
    p = subprocess.Popen(f"latexmk -pdf -output-directory={os.path.join(os.getcwd(), 'out')} {tmp_tex.name}", shell=True)
    try:
      p.wait(30)
    except subprocess.TimeoutExpired:
      logging.error("Latex Compile timedout")
      p.kill()
      logging.error("Copying output to debug.tex")
      shutil.copy(f"{tmp_tex.name}", "debug.tex")
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
    
    questions_by_subject = {
      s : list(filter((lambda q: q.subject == s), question_set))
      for s in  set([q.subject for q in question_set])
    }
    for s in questions_by_subject.keys():
      logging.info(f"subject: {s} {sum(map((lambda q: q.value), questions_by_subject[s]))}")
      counts_by_value = {
        # todo: there's a better way to do this, but I doubt I need to ever scale it up
        val : len(list(filter((lambda q: q.value == val), questions_by_subject[s])))
        for val in set([q.value for q in questions_by_subject[s]])
      }
      for val in sorted(counts_by_value.keys(), reverse=True):
        logging.info(f"  {counts_by_value[val]}x {val}points")
    logging.info(f"total: {sum(map((lambda q: q.value), question_set))}")
    
  
  writer = pypdf.PdfWriter()
  for pdf_file in [os.path.join("out", f) for f in os.listdir("out") if f.endswith(".pdf")]:
    writer.append(pdf_file)
  
  writer.write("exam.pdf")
  #shutil.rmtree("out")
  


if __name__ == "__main__":
  main()
