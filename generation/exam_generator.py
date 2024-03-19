#!env python
import logging
import os
import shutil
import tempfile
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
  parser.add_argument("--questions_file", default="templates/questions.yaml")
  parser.add_argument("--debug", action="store_true")
  return parser.parse_args()


def generate_exam(questions_file):
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
    key=lambda q: (-q.value, ["memory", "io"].index(q.subject))
  )
  
  def make_questions(*args, **kwargs):
    ## In this function we'll make the questions for the exam
    questions = [q.generate_latex() for q in question_set]
    
    return '\n\n'.join(questions)
  
  env.globals["generate_exam"] = make_questions
  template = env.get_template('exam_base.j2')
  
  rendered_output = template.render()
  return rendered_output


def main():
  args = parse_args()
  
  if os.path.exists("out"): shutil.rmtree("out")
  os.mkdir("out")
  
  for _ in range(args.num_exams):
    exam_text = generate_exam(questions_file=args.questions_file)
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
    subprocess.Popen(f"latexmk -c {tmp_tex.name} -output-directory={os.path.join(os.getcwd(), 'out')}", shell=True)
    tmp_tex.close()
  
  writer = pypdf.PdfWriter()
  for pdf_file in [os.path.join("out", f) for f in os.listdir("out") if f.endswith(".pdf")]:
    writer.append(pdf_file)
  
  writer.write("exam.pdf")
  #shutil.rmtree("out")


if __name__ == "__main__":
  main()
