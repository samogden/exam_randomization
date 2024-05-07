#!env python
from typing import List


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
      logging.error("Cannot interpret input as float")
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
  
  def __str__(self):
    return f"{self.name} ::= {self.true_value}"
  
  def get_markdown_answers(self) -> List[str]:
    # todo: generate variations
    return [f"* {self.true_value}\n"]