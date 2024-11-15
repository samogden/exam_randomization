#!env python
from typing import List

from .question import Question, CanvasQuestion
from .variable import Variable, VariableBytes, VariableFloat

import random
import math

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


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
      f"Given that we have {self.num_bits_var if self.from_binary else self.num_bytes_var} {'bits' if self.from_binary else 'Bytes'}, "
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

class AverageMemoryAccessTime(CanvasQuestion):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    orders_of_magnitude_different = random.randint(1,4)
    self.hit_latency = random.randint(1,9)
    self.miss_latency = int(random.randint(1, 9) * math.pow(10, orders_of_magnitude_different))
    
    if random.random() > 0.5:
      # Then let's make it very close to 99%
      self.hit_rate = (99 + random.random()) / 100
    else:
      self.hit_rate = random.random()
    self.hit_rate = round(self.hit_rate, 4)
  
    self.amat = self.hit_rate * self.hit_latency + (1 - self.hit_rate) * self.miss_latency
    self.amat_var = VariableFloat("Average Memory Access Time", true_value=self.amat)
    self.blank_vars.update({
      "amat" : self.amat_var
    })
    
    log.debug(f"orders_of_magnitude_different: {orders_of_magnitude_different}")
    log.debug(f"self.hit_latency: {self.hit_latency}")
    log.debug(f"self.miss_latency: {self.miss_latency}")
    log.debug(f"self.hit_rate: {self.hit_rate}")
  
  def get_question_body(self, *args, **kwargs) -> List[str]:
    lines = [
      "Please calculate the Average Memory Access Time given the below information.  Please round your answer to 2 decimal points.",
      "<ul>",
    ]
    
    info_lines = [
      f" <li>Hit Latency: {self.hit_latency} cycles</li>"
      f" <li>Miss Latency: {self.miss_latency} cycles</li>"
    ]
    if random.random() > 0.5:
      info_lines.append(f" <li>Hit Rate: {100 * self.hit_rate: 0.2f}% </li>")
    else:
      info_lines.append(f" <li>Miss Rate: {100 * (1 - self.hit_rate): 0.2f}% </li>")
    
    lines.extend(random.sample(info_lines, len(info_lines)))
    lines.append("</ul>")
    
    lines.extend([
      "",
      "Average Memory Access Time: [amat]cycles"
    ])
    
    return lines
  
  def get_explanation(self, *args, **kwargs) -> List[str]:
    lines = [
      "Remember that to calculate the Average Memory Access Time we weight both the hit and miss times by their relative likelihood.",
      "That is, we calculate <tt>(hit_rate)*(hit_cost) + (1 - hit_rate)*(miss_cost)</tt>."
      "",
      "In this case, that calculation becomes:",
      f"({self.hit_rate: 0.4f})*({self.hit_latency}) + ({1 - self.hit_rate: 0.4f})*({self.miss_latency}) = {self.amat:0.2f}cycles"
    ]
    return lines
  

def main():
  pass

if __name__ == "__name__":
  pass