#!env python
from typing import List

from .question import Question, CanvasQuestion
from .variable import Variable, VariableBytes

import random
import math

import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


class BitsAndBytes(CanvasQuestion):
  MIN_BITS = 3
  MAX_BITS = 49
  
  def __init__(
      self,
      num_bits=None,
      *args, **kwargs
  ):
    super().__init__(given_vars=[], target_vars=[], *args, **kwargs)
    self.from_binary = 0 == random.randint(0,1)
    
    if num_bits is None:
      self.num_bits = random.randint(self.MIN_BITS, self.MAX_BITS)
      self.num_bytes = int(math.pow(2, self.num_bits))
    
    self.num_bits_var = Variable("Number of bits", self.num_bits)
    self.num_bytes_var = VariableBytes("Number of Bytes", self.num_bytes)
    
    if self.from_binary:
      self.blank_vars.update({
        "answer" : self.num_bytes_var
      })
    else:
      self.blank_vars.update({
        "answer" : self.num_bits_var
      })
      
  
  def get_question_body(self, *args, **kwargs) -> List[str]:
    question_lines = []
    
    question_lines = [
      f"Given that we have {self.num_bits_var if self.from_binary else self.num_bytes_var}{'bits' if self.from_binary else 'Bytes'}, "
      f"how many {'bits' if not self.from_binary else 'Bytes'} "
      f"{'do we need to address our memory' if not self.from_binary else 'of memory can be address'}?"
    ]
    
    question_lines.extend([
      f"{'Address space size' if self.from_binary else 'Number of bits in address'}: [answer]{'bits' if not self.from_binary else 'Bytes'}"
    ])
    return question_lines
    
    
  def get_explanation(self, *args, **kwargs) -> List[str]:
    explanation_lines = [
      "Remember that for these problems we use one of these two equations (which are equivalent)",
      "<ul>"
      r"<li> \( log_{2}(\text{#Bytes}) = \text{#bits} \) </li>",
      r"<li> \( 2^{(\text{#bits})} = \text{#Bytes} \) </li>",
      "</ul>",
      "Therefore, we calculate:",
    ]
    
    if self.from_binary:
      explanation_lines.extend([
        f"\\( 2 ^ {{{self.num_bits}bits}} = \\textbf{{{self.num_bytes}}}Bytes \\)"
      ])
    else:
      explanation_lines.extend([
        f"\\( log_{2}({self.num_bytes}Bytes) = \\textbf{{{self.num_bits}}}bits \\)"
      ])
    
    return explanation_lines

class HexAndBinary(CanvasQuestion):
  MIN_HEXITS = 1
  MAX_HEXITS = 8
  
  def __init__(self, *args, **kwargs):
    super().__init__(given_vars=[], target_vars=[], *args, **kwargs)
    self.from_binary = 0 == random.randint(0,1)
    
    self.number_of_hexits = random.randint(self.MIN_HEXITS, self.MAX_HEXITS)
    self.value = random.randint(1, 16**self.number_of_hexits)
    
    self.hex_var = Variable("Hex Value", f"0x{self.value:0{self.number_of_hexits}X}")
    self.binary_var = Variable("Binary Value", f"0b{self.value:0{4*self.number_of_hexits}b}")
    
    self.blank_vars.update({
      "answer" : self.hex_var if self.from_binary else self.binary_var
    })
  
  def get_question_body(self, *args, **kwargs) -> List[str]:
    
    question_lines = [
      f"Given the number {self.hex_var if not self.from_binary else self.binary_var} please convert it to {'hex' if self.from_binary else 'binary'}.",
      "Please include base indicator all padding zeros as appropriate (e.g. 0x01 should be 0b00000001"
    ]
    
    question_lines.extend([
      f"Value in {'hex' if self.from_binary else 'binary'}: [answer]"
    ])
    return question_lines
  
  def get_explanation(self, *args, **kwargs) -> List[str]:
    explanation_lines = [
      "The core idea for converting between binary and hex is to divide and conquer.  "
      "Specifically, each hexit (hexadecimal digit) is equivalent to 4 bits.  "
    ]
    
    if self.from_binary:
      explanation_lines.extend([
        "Therefore, we need to consider each group of 4 bits together and convert them to the appropriate hexit."
      ])
    else:
      explanation_lines.extend([
        "Therefore, we need to consider each hexit and convert it to the appropriate 4 bits."
      ])
    
    binary_str = f"{self.value:0{4*self.number_of_hexits}b}"
    hex_str = f"{self.value:0{self.number_of_hexits}X}"
    explanation_lines.extend(
      self.get_table_lines(
        table_data={
          "0b" : [binary_str[i:i+4] for i in range(0, len(binary_str), 4)],
          "0x" : hex_str
        },
        sorted_keys=["0b", "0x"][::(1 if self.from_binary else -1)],
        add_header_space=False
      )
    )
    if self.from_binary:
      explanation_lines.extend([
        f"Which gives us our hex value of: 0x{hex_str}"
      ])
    else:
      explanation_lines.extend([
        f"Which gives us our binary value of: 0b{binary_str}"
      ])
    
    return explanation_lines

def main():
  pass

if __name__ == "__name__":
  pass