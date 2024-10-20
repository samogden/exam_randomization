#!env python
from __future__ import annotations

import enum
import itertools
import math
import random
from typing import List

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

logging.getLogger("matplotlib").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

class Variable:
  def __init__(self, name, true_value, *args, **kwargs):
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
    return f"{self.true_value}"
  
  def get_info(self):
    return (self.name, self.id, self.true_value)
  
  def get_answers(self) -> List[str]:
    return [f"{self.true_value}"]
  
  def get_markdown_answers(self) -> List[str]:
    return [f"* {ans}\n" for ans in self.get_answers()]
  
  # todo: Add in a "get raw" function that returns the valye, if available, and a "get formatted" version that using a formating string

class VariableFloat(Variable):
  default_sigfigs = 1
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
  
  def get_markdown_answers(self, sigfigs=None) -> List[str]:
    # todo: make canvas friendly
    if sigfigs is None:
      sigfigs = self.default_sigfigs
    return [f"= {self.true_value:.{sigfigs}f} +- {self.epsilon}\n"]
  
  def get_answers(self, sigfigs=None) -> List[str]:
    if sigfigs is None:
      sigfigs = self.default_sigfigs
    
    num_sig_figs = 1 #+ math.ceil(abs(math.log10(self.epsilon)))
    
    # https://chatgpt.com/share/40e95507-a88b-41eb-b469-b56f7d4a9dea
    def write_floats(start, end, granularity):
      # Generate the numbers in the range with the specified granularity
      numbers = []
      current = start
      while current <= end:
        numbers.append(round(current, len(str(granularity).split('.')[1])))
        current += granularity
      
      # Format each number with all possible significant figures
      result = []
      for number in numbers:
        str_number = f"{number:.{len(str(granularity).split('.')[1])}f}"
        result.append(str_number)
        integer_part, decimal_part = str_number.split('.')
        if int(decimal_part) == 0:
          result.append(str(int(number)))
        else:
          for i in range(1, len(decimal_part)+1):
            result.append(f"{integer_part}.{decimal_part[:i]}")
      
      # Remove duplicates and sort
      result = sorted(set(result))
      
      return result
    
    # answers = write_floats(self.true_value - self.epsilon, self.true_value + self.epsilon, 10**(-num_sig_figs))
    answers = [f"{self.true_value:0.2f}"]
    return answers
    

class VariableHex(Variable):
  class PRESENTATION(enum.Enum):
    HEX = enum.auto()
    BINARY = enum.auto()
    DECIMAL = enum.auto()
  def __init__(self, *args, num_bits=0, default_presentation=PRESENTATION.HEX, **kwargs):
    super().__init__(*args, **kwargs)
    self.num_bits = num_bits
    self.default_presentation = default_presentation
  
  def __str__(self):
    if self.default_presentation == VariableHex.PRESENTATION.HEX:
      return f"0x{self.true_value:X}"
    elif self.default_presentation == VariableHex.PRESENTATION.DECIMAL:
      return f"{self.true_value}"
    elif self.default_presentation == VariableHex.PRESENTATION.BINARY:
      return f"0b{self.true_value:0{self.num_bits}b}"
  
  def get_answers(self) -> List[str]:
    return [
      f"{self.true_value}",
      f"0x{self.true_value:X}",
      f"0b{self.true_value:0{self.num_bits}b}"
    ]

class VariableBytes(Variable):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
  
  def get_answers(self) -> List[str]:
    def bytes_to_human_readable(size_in_bytes):
      # Define the SI units
      SI_UNITS = ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
      
      # Start at the smallest unit (bytes)
      unit_index = 0
      
      # Divide the size by 1000 while it's large enough to convert to the next unit
      while size_in_bytes >= 1024 and unit_index < len(SI_UNITS) - 1:
        size_in_bytes /= 1024
        unit_index += 1
      
      # Format the number with two decimal places
      return f"{size_in_bytes:.0f}{SI_UNITS[unit_index]}"
    return [
      f"{self.true_value}",
      f"{bytes_to_human_readable(self.true_value)}",
      f"{self.true_value}B",
      f"{bytes_to_human_readable(self.true_value)}B",
      f"{self.true_value}Bytes",
      f"{bytes_to_human_readable(self.true_value)}Bytes",
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
    variations.extend([' |'.join(p) for p in itertools.permutations(self.productions)])
    variations.extend(['| '.join(p) for p in itertools.permutations(self.productions)])
    
    variations.extend([' | '.join([p_sub.replace('`','') for p_sub in p]) for p in itertools.permutations(self.productions)])
    variations.extend(['|'.join([p_sub.replace('`','') for p_sub in p]) for p in itertools.permutations(self.productions)])
    variations.extend([' |'.join([p_sub.replace('`','') for p_sub in p]) for p in itertools.permutations(self.productions)])
    variations.extend(['| '.join([p_sub.replace('`','') for p_sub in p]) for p in itertools.permutations(self.productions)])
    return [f"{answer}" for answer in variations]

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
    # todo: make canvas compatible
    lines = []
    lines.extend([
      f"[*] {answer}" for answer in self.correct_choices
    ])
    lines.extend([
      f"[ ] {answer}" for answer in self.incorrect_choices
    ])
    
    return sorted(lines, key=(lambda _: random.random()))

