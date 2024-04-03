import random
import math


class QuickFunctions:
  
  @classmethod
  def add_spaces_to_str(cls, input_str, every=4):
    if len(input_str) < 2*every:
      return input_str
    return ' '.join([input_str[i:i+every] for i in range(0, len(input_str), every)])
  
  @classmethod
  def random_binary_number(cls, num_bits):
    # return random.randrange(0, int(math.pow(2, num_bits)))
    return '0b ' + cls.add_spaces_to_str(cls.random_binary_bits(num_bits))
  
  @classmethod
  def random_binary_bits(cls, num_bits):
    return ''.join(random.choices("01", k=num_bits))
  @classmethod
  def random_hex_number(cls, num_digits):
    return '0x' + cls.random_hex_digits(num_digits)
  
  @classmethod
  def random_hex_digits(cls, num_digits):
    return ''.join(random.choices("0123456789abcdef".upper(), k=num_digits))
  
  @classmethod
  def pick_replacement_algo(cls):
    return cls.pick_a_choice(["LRU", "FIFO", "Belady"])
  
  @classmethod
  def pick_a_choice(cls, list_of_choices):
    return str(random.choice(list_of_choices))
  
  @classmethod
  def number_in_range(cls, lower_bound, upper_bound):
    return random.randrange(lower_bound, upper_bound)
  
  @classmethod
  def print_as_hex(cls, in_number, pad_to_length=0, show_prefix=True, add_spaces=False):
    out_str = f"{in_number : x}".zfill(pad_to_length)
    if add_spaces:
      out_str = ' ' + cls.add_spaces_to_str(out_str)
    if show_prefix:
      out_str = '0x' + out_str
    return out_str
  
  @classmethod
  def print_as_binary(cls, in_number, pad_to_length=0, show_prefix=True, add_spaces=False, every=4):
    out_str = f"{in_number : b}".zfill(pad_to_length)
    if add_spaces:
      out_str = ' ' + cls.add_spaces_to_str(out_str)
    if show_prefix:
      out_str = '0b' + out_str
    return out_str
