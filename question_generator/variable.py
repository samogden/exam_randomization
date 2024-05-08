#!env python
import itertools
import random
from typing import List

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.WARNING)

class Variable:
  def __init__(self, name, true_value):
    self.name = name
    self.true_value = true_value
    self.given_value = None
    self.id = id(self)
  def answer_question(self, given_value):
    self.given_value = given_value
  def compare(self):
    self.result = str(self.given_value) == str(self.true_value)
    return self.result
  def get_feedback(self):
    if self.compare():
      return f"Correct! {self.true_value} == {self.given_value}"
    else:
      return f"Incorrect! {self.true_value} != {self.given_value} (your answer)"
  
  def __str__(self):
    return f"{self.name}: {self.true_value}"
  
  def get_info(self):
    return (self.name, self.id, self.true_value)
  
  def get_markdown_answers(self) -> List[str]:
    return [f"* {self.true_value}\n"]
  
  # todo: Add in a "get raw" function that returns the valye, if available, and a "get formatted" version that using a formating string

class VariableFloat(Variable):
  precision = 3
  def __init__(self, name, true_value, epsilon=0.1):
    self.epsilon = epsilon
    super().__init__(name, true_value)
  def answer_question(self, given_value):
    try:
      self.given_value = float(given_value)
    except ValueError:
      log.error("Cannot interpret input as float")
      self.given_value = float("nan")
  def compare(self):
    self.result = (self.true_value - self.epsilon <= self.given_value) and (self.given_value <= self.true_value + self.epsilon)
    return self.result
  def get_feedback(self):
    if self.compare():
      return f"Correct! {self.true_value: 0.3f} == {self.given_value: 0.3f}"
    else:
      return f"Incorrect! {self.true_value: 0.3f} != {self.given_value: 0.3f} (your answer)"
  
  def get_markdown_answers(self, precision=None) -> List[str]:
    if precision is None:
      precision = self.precision
    return [f"= {self.true_value:.{precision}f} +- {self.epsilon}\n"]

class VariableHex(Variable):
  def __init__(self, *args, num_bits=0, **kwargs):
    super().__init__(*args, **kwargs)
    self.num_bits = num_bits
  def get_markdown_answers(self) -> List[str]:
    return [
      f"* {self.true_value}",
      f"* {self.true_value:x}",
      f"* 0x{self.true_value:X}",
      f"* {self.true_value:0{self.num_bits}b}",
      f"* 0b{self.true_value:0{self.num_bits}b}"
    ]

class Variable_BNFRule(Variable):
  
  def __init__(self, name, productions : List[str]):
    self.productions = productions
    super().__init__(name, ' | '.join(self.productions))
  
  
  def __str__(self):
    return f"{self.name} ::= {self.true_value}"
  
  def get_markdown_answers(self) -> List[str]:
    # todo: generate variations
    variations = []
    variations.extend([' | '.join(p) for p in itertools.permutations(self.productions)])
    variations.extend(['|'.join(p) for p in itertools.permutations(self.productions)])
    return [f"* {answer}" for answer in variations]

class Variable_BNFstr(Variable):
  # todo: this should probably be more separate
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.correct_choices = []
    self.incorrect_choices = []
  def add_choice(self, choice : str, is_correct : bool):
    if is_correct:
      self.correct_choices.append(choice)
    else:
      self.incorrect_choices.append(choice)
    
  def get_markdown_answers(self) -> List[str]:
    lines = []
    lines.extend([
      f"[*] {answer}" for answer in self.correct_choices
    ])
    lines.extend([
      f"[ ] {answer}" for answer in self.incorrect_choices
    ])
    
    return sorted(lines, key=(lambda _: random.random()))