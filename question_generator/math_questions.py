#!env python
from typing import List

from question import Question
from variable import Variable

import random
import math

import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


class BitsAndBytes(Question):
  MIN_BITS = 3
  MAX_BITS = 20
  
  def __init__(
      self,
      num_bits=None
  ):
    if num_bits is None:
      num_bits = random.randint(self.MIN_BITS, self.MAX_BITS)
    self.num_bits = Variable("Number of bits", num_bits)
    self.num_bytes = Variable("Number of bytes", int(math.pow(2, self.num_bits.true_value)))
    super().__init__(given_vars=[self.num_bits, self.num_bytes])
    
  def get_explanation(self) -> List[str]:
    explanation_lines = [
      "Remember that for these problems we use one of these two equations (which are equivalent)",
      "1. log2(`Number of bytes`) = `Number of bits`",
      "2. 2 ^ (`Number of bits`) = `Number of bytes`",
      "Therefore, we calculate",
    ]
    
    if self.num_bits in self.given_vars:
      explanation_lines.extend([
        f"2 ^ ({self.num_bits.true_value}) = ***{self.num_bytes.true_value}***"
      ])
    else:
      explanation_lines.extend([
        f"log2({self.num_bytes.true_value}) = ***{self.num_bits.true_value}***"
      ])
    
    return explanation_lines

class HexAndBinaryQuestions(Question):
  MIN_HEXITS = 1
  MAX_HEXITS = 8
  
  def __init__(self):
    self.number_of_hexits = random.randint(self.MIN_HEXITS, self.MAX_HEXITS)
    
    self.value = random.randint(1, 16**self.number_of_hexits)
    
    self.hex_var = Variable("Hex Value", f"0x{self.value:0{self.number_of_hexits}X}")
    self.binary_var = Variable("Binary Value", f"0b{self.value:0{4*self.number_of_hexits}b}")
    
    super().__init__(
      given_vars=[
        self.hex_var,
        self.binary_var
      ]
    )
  
  def get_explanation(self) -> List[str]:
    explanation_lines = [
      "The core idea for converting between binary and hex is to divide and conquer.  "
      "Specifically, each hexit (hexadecimal digit) is equivalent to 4 bits.  "
      "So, we just need to consider each hexit individually, or groups of 4 bits.",
      "",
    ]
    
    binary_str = f"{self.value:0{4*self.number_of_hexits}b}"
    hex_str = f"{self.value:0{self.number_of_hexits}X}"
    if self.hex_var in self.target_vars:
      explanation_lines.extend([
        f"Starting with our binary value, {self.binary_var.true_value}, if we split this into groups of 4 we get:\n",
        '|`' + f"{'`|`'.join([binary_str[i:i+4] for i in range(0, len(binary_str), 4)])}" + '`|\n' +
        '|:----:' * len(hex_str) + '|\n' +
        '|   `' + '`|   `'.join(hex_str) + '`|\n',
        f"Which gives us our hex value of: `0x{hex_str}`"
      ])
    
    if self.binary_var in self.target_vars:
      explanation_lines.extend([
        f"Starting with our hex value, {self.hex_var.true_value}, if we split this into individual hexits we get: ",
        '|   `' + '`|   `'.join(hex_str) + '`|\n' +
        '|:----:' * len(hex_str) + '|\n' +
        '|`' + f"{'`|`'.join([binary_str[i:i+4] for i in range(0, len(binary_str), 4)])}" + '`|\n',
        f"Which gives us our binary value of: `0b{binary_str}`"
      ])
    
    
    return explanation_lines

def main():
  pass

if __name__ == "__name__":
  pass