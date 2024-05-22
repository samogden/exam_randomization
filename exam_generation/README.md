# Exam Generation

To generate exams use the below command:

```python exam_generator.py```

## More information

More information can be found with flags.
Currently it takes in latex-style strings (that are escaped like woah), but I'm hoping to move to using a more robust solution for intermedite solutions, and being able to output stuff besides latex.

```
$ python exam_generator.py --help
usage: exam_generator.py [-h] [--num_exams NUM_EXAMS] [--questions_file QUESTIONS_FILE] [--debug]

options:
  -h, --help            show this help message and exit
  --num_exams NUM_EXAMS
  --questions_file QUESTIONS_FILE
  --debug
```

## Note

You have to have `latexmk` installed on your system to run this tool.