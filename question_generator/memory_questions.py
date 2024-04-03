#!env python
from typing import List

from question_generator import Question
from question_generator import Variable, VariableHex

import random
import math

import logging

logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)


class VirtualAddress_parts(Question):
  MAX_BITS = 64
  
  def __init__(
      self,
      num_va_bits=None,
      num_offset_bits=None,
      num_vpn_bits=None
  ):
    
    if (num_va_bits is None) and (num_offset_bits is None) and (num_vpn_bits is None):
      num_va_bits = random.randint(1, self.MAX_BITS)
    
    # If we have a VA (or have generated one)
    if (num_offset_bits is None) and (num_vpn_bits is None):
      num_offset_bits = random.randint(1, num_va_bits)
    
    if (num_vpn_bits is None):
      num_vpn_bits = num_va_bits - num_offset_bits
    
    self.num_va_bits = Variable("# VA bits", num_va_bits)
    self.num_offset_bits = Variable("# offset bits", num_offset_bits)
    self.num_vpn_bits = Variable("# VPN bits", num_vpn_bits)
    
    super().__init__(
      given_vars=[
        self.num_va_bits,
        self.num_offset_bits,
        self.num_vpn_bits
      ]
    )
  
  def get_explanation(self) -> List[str]:
    
    line_to_add = ""
    if self.num_va_bits in self.target_vars:
      line_to_add += f"***{self.num_va_bits.true_value}***"
    else:
      line_to_add += f"{self.num_va_bits.true_value}"
    
    line_to_add += " = "
    
    if self.num_vpn_bits in self.target_vars:
      line_to_add += f"***{self.num_vpn_bits.true_value}***"
    else:
      line_to_add += f"{self.num_vpn_bits.true_value}="
    
    line_to_add += " + "
    
    if self.num_offset_bits in self.target_vars:
      line_to_add += f"***{self.num_offset_bits.true_value}***"
    else:
      line_to_add += f"{self.num_offset_bits.true_value}"
      
    return [
      "VA = VPN + offset",
      line_to_add
    ]

class MemoryAccessQuestion(Question):
  PROBABILITY_OF_INVALID = .25

class BaseAndBounds(MemoryAccessQuestion):
  MAX_BITS = 32
  MAX_BOUNDS_BITS = 16
  
  def __init__(
      self
  ):
    
    bounds_bits = random.randint(1, self.MAX_BOUNDS_BITS)
    base_bits = self.MAX_BITS - bounds_bits
    
    self.bounds = int(math.pow(2, bounds_bits))
    self.base = random.randint(1, int(math.pow(2, base_bits))) * self.bounds
    self.virtual_address = random.randint(1, int(self.bounds / self.PROBABILITY_OF_INVALID))
    
    self.bounds_var = Variable("bounds", f"0x{self.bounds :X}")
    self.base_var = Variable("Base", f"0x{self.base :X}")
    self.virtual_address_var = Variable("Virtual Address", f"0x{self.virtual_address :X}")
    
    if self.virtual_address > self.bounds:
      self.physical_address_var = Variable("Physical Address", "INVALID")
    else:
      self.physical_address_var = VariableHex("Physical Address", self.base + self.virtual_address)
    
    
    super().__init__(
      given_vars=[
        self.base_var,
        self.bounds_var,
        self.virtual_address_var
      ],
      target_vars=[
        self.physical_address_var
      ]
    )
  
  def get_explanation(self) -> List[str]:
    explanation_lines = [
      "There's two steps to figuring out base and bounds.",
      "1. Are we within the bounds?",
      "2. If so, add to our base.",
      "",
    ]
    if self.virtual_address < self.bounds:
      explanation_lines.extend([
          f"Step 1: {self.virtual_address_var.true_value} < {self.bounds_var.true_value} --> {'***VALID***' if (self.virtual_address < self.bounds) else 'INVALID'}",
          "",
          f"Step 2: Since the previous check passed, we calculate {self.base_var.true_value} + {self.virtual_address_var.true_value} = ***0x{self.base + self.virtual_address:X}***.  If it had been invalid we would have simply written INVALID"
        ]
      )
    else:
      explanation_lines.extend([
          f"Step 1: {self.virtual_address_var.true_value} < {self.bounds_var.true_value} --> {'VALID' if (self.virtual_address < self.bounds) else '***INVALID***'}",
          "",
          f"Step 2: Since the previous check failed, we simply write ***INVALID***.  If it had been valid, we would have calculated {self.base_var.true_value} + {self.virtual_address_var.true_value} = 0x{self.base + self.virtual_address:X}"
        ]
      )
    return explanation_lines

class Paging(MemoryAccessQuestion):
  
  
  MIN_OFFSET_BITS = 3
  MIN_VPN_BITS = 3
  MIN_PFN_BITS = 3
  
  MAX_OFFSET_BITS = 8
  MAX_VPN_BITS = 8
  MAX_PFN_BITS = 16
  
  def __init__(self, num_offset_bits=None, num_vpn_bits=None, num_pfn_bits=None):
    if num_offset_bits == None:
      self.num_offset_bits = random.randint(self.MIN_OFFSET_BITS, self.MAX_OFFSET_BITS)
    if num_vpn_bits == None:
      self.num_vpn_bits = random.randint(self.MIN_VPN_BITS, self.MAX_VPN_BITS)
    if num_pfn_bits == None:
      self.num_pfn_bits = random.randint(max([self.MIN_PFN_BITS, self.num_vpn_bits]), self.MAX_PFN_BITS)
    
    self.virtual_address = random.randint(0, 2**(self.num_vpn_bits + self.num_offset_bits))
    
    # Calculate these two
    self.offset = self.virtual_address % (2**(self.num_offset_bits))
    self.vpn = self.virtual_address // (2**(self.num_offset_bits))
    
    # Generate this randomly
    self.pfn = random.randint(0, 2**(self.num_pfn_bits))
    
    # Calculate this
    self.physical_address = self.pfn * (2**self.num_offset_bits) + self.offset
    
    # Set up variables for display
    self.vpn_bits_var = Variable("# VPN bits", self.num_vpn_bits)
    self.pfn_bits_var = Variable("# PFN bits", self.num_pfn_bits)
    self.offset_bits_var = Variable("# offset bits", self.num_offset_bits)
    
    self.virtual_address_var = VariableHex("Virtual Address", f"0b{self.virtual_address:0{self.num_vpn_bits+self.num_offset_bits}b}")
    self.pfn_var = VariableHex("PFN", f"0b{self.pfn:0{self.num_pfn_bits}b}")
    
    if random.choices([True, False], weights=[(1-self.PROBABILITY_OF_INVALID), self.PROBABILITY_OF_INVALID], k=1)[0]:
      # Set our actual entry to be in the table and valid
      self.pte = self.pfn + (2**(self.num_pfn_bits))
      self.physical_address_var = VariableHex("Physical Address", self.physical_address, num_bits=(self.num_pfn_bits+self.num_offset_bits))
    else:
      # Leave it as invalid
      self.pte = self.pfn
      self.physical_address_var = Variable("Physical Address", "INVALID")
    
    
    # logging.debug(f"va: {self.virtual_address:{self.num_vpn_bits+self.num_offset_bits}b}")
    # logging.debug(f"    {self.vpn:0{self.num_vpn_bits}b}{self.offset:0{self.num_offset_bits}b}")
    # logging.debug(f"    {self.vpn:0{self.num_vpn_bits}b}|{self.offset:0{self.num_offset_bits}b}")
    # logging.debug(f"{self.vpn:0{self.num_vpn_bits}b} --> {self.pfn:0{self.num_pfn_bits}b}")
    # logging.debug(f"{self.physical_address:0{self.num_pfn_bits+self.num_offset_bits}b}")
    
    super().__init__(
      given_vars=[
        self.vpn_bits_var,
        self.pfn_bits_var,
        self.offset_bits_var,
        self.virtual_address_var,
        self.pfn_var,
      ],
      target_vars=[
        self.physical_address_var
      ]
    )
  
  def get_explanation(self) -> List[str]:
    explanation_lines = [
      "The core idea of Paging is we want to break the virtual address into the VPN and the offset.  "
      "We then attach the PFN to the offset and have our physical address.",
      "",
      "Don't forget to pad with the appropriate number of 0s (the appropriate number is the number of bits)!",
      "",
      f"Virtual Address = VPN | offset",
      f"0b{self.virtual_address:0{self.num_vpn_bits+self.num_offset_bits}b} = 0b{self.vpn:0{self.num_vpn_bits}b} | 0b{self.offset:0{self.num_offset_bits}b}",
      "",
      "Physical Address = PFN | offset",
      f"***0b{self.physical_address:0{self.num_pfn_bits+self.num_offset_bits}b}*** = 0b{self.pfn:0{self.num_pfn_bits}b} | 0b{self.offset:0{self.num_vpn_bits}b}",
      "",
      "",
      "Note: Strictly speaking, this calculation is:",
      f"***0b{self.physical_address:0{self.num_pfn_bits+self.num_offset_bits}b}*** = 0b{self.pfn:0{self.num_pfn_bits}b}{0:0{self.num_offset_bits}} + 0b{self.offset:0{self.num_offset_bits}b}",
      "But that's a lot of extra 0s, so I'm splitting them up for succinctness",
      ""
    ]
    return explanation_lines

class Paging_with_table(Paging):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.given_vars.remove(self.pfn_var)
  
  def get_question_body(self) -> List[str]:
    markdown_lines = super().get_question_body()
    
    
    table_size = random.randint(5,10)
    table_bottom = self.vpn - random.randint(0, table_size)
    if table_bottom < 0:
      table_bottom = 0
    table_top = min([table_bottom + table_size, 2**self.num_vpn_bits])
    
    page_table = {}
    page_table[self.vpn] = self.pte
      
      # Fill in the rest of the table
    # for vpn in range(2**self.num_vpn_bits):
    for vpn in range(table_bottom, table_top):
      if vpn == self.vpn: continue
      pte = page_table[self.vpn]
      while pte in page_table.values():
        pte = random.randint(0, 2**self.num_pfn_bits-1)
        if random.choices([True, False], weights=[(1-self.PROBABILITY_OF_INVALID), self.PROBABILITY_OF_INVALID], k=1)[0]:
          # Randomly set it to be valid
          pte += (2**(self.num_pfn_bits))
      # Once we have a unique random entry, put it into the Page Table
      page_table[vpn] = pte
    
    table_lines = ""
    table_lines += "| VPN | PTE |\n"
    table_lines += "|:---- | :----|\n"
    # table_lines += "...  | ...\n"
    for vpn in sorted(page_table.keys()):
      pte = page_table[vpn]
      table_lines += f"|`0b{vpn:0{self.num_vpn_bits}b}` | `0b{pte:0{(self.num_pfn_bits+1)}b}`|\n"
    
    # table_lines += "...  | ...\n"
    
    # table_lines += f"0b{self.vpn:0{self.num_vpn_bits}b} | 0b{self.pfn:0{self.num_pfn_bits}b}\n"
    
    markdown_lines.append(table_lines)
    return markdown_lines
  
  
  def get_explanation(self) -> List[str]:
    explanation_lines = [
      "The core idea of Paging is we want to break the virtual address into the VPN and the offset.  "
      "From here, we get the Page Table Entry corresponding to the VPN, and check the validity of the entry.  "
      "If it is valid, we clear the metadata and attach the PFN to the offset and have our physical address.",
      "",
      "Don't forget to pad with the appropriate number of 0s (the appropriate number is the number of bits)!",
      "",
      f"Virtual Address = VPN | offset",
      f"0b{self.virtual_address:0{self.num_vpn_bits+self.num_offset_bits}b} = 0b{self.vpn:0{self.num_vpn_bits}b} | 0b{self.offset:0{self.num_offset_bits}b}",
      ""
    ]
    
    explanation_lines.extend([
      "We next use our VPN to index into our page table and find the corresponding entry."
      f"Our Page Table Entry is: `0b{self.vpn:0{self.num_vpn_bits}b}` | `0b{self.pte:0{(self.num_pfn_bits+1)}b}`, where the first value is our VPN and the second is our PTE.",
      "",
    ])
    
    is_valid = (self.pte // (2**self.num_pfn_bits) == 1)
    if is_valid:
      explanation_lines.extend([
        f"In our PTE we see that the first bit is ***{self.pte // (2**self.num_pfn_bits)}*** meaning that the translation is ***VALID***"
      ])
    else:
      explanation_lines.extend([
        f"In our PTE we see that the first bit is ***{self.pte // (2**self.num_pfn_bits)}*** meaning that the translation is ***INVALID***.",
        "Therefore, we just write \"INVALID\" as our answer.",
        "If it were valid we would complete the below steps.",
        "",
        "===================================================="
        "\n",
      ])
    
    explanation_lines.extend([
      "Next, we convert our PTE to our PFN by removing our metadata.  In this case we're just removing the leading bit.  We can do this by applying a binary mask.",
      f"PFN = PTE & mask",
      f"0b{self.pfn} = 0b{self.pte:0{self.num_pfn_bits+1}b} & 0b{(2**self.num_pfn_bits)-1:0{self.num_pfn_bits+1}b}"
    ])
    
    explanation_lines.extend([
      "We then add combine our PFN and offset",
      "",
      "Physical Address = PFN | offset",
      f"{'***' if is_valid else ''}0b{self.physical_address:0{self.num_pfn_bits+self.num_offset_bits}b}{'***' if is_valid else ''} = 0b{self.pfn:0{self.num_pfn_bits}b} | 0b{self.offset:0{self.num_vpn_bits}b}",
      "",
      "",
      "Note: Strictly speaking, this calculation is:",
      f"{'***' if is_valid else ''}0b{self.physical_address:0{self.num_pfn_bits+self.num_offset_bits}b}{'***' if is_valid else ''} = 0b{self.pfn:0{self.num_pfn_bits}b}{0:0{self.num_offset_bits}} + 0b{self.offset:0{self.num_offset_bits}b}",
      "But that's a lot of extra 0s, so I'm splitting them up for succinctness",
      ""
    ])
    return explanation_lines

if False:
  class Segmentation(MemoryAccessQuestion):
    MIN_VIRTUAL_ADDRESS_BITS = 3
    MAX_VIRTUAL_ADDRESS_BITS = 8
    def __init__(self, num_virtual_bits=None):
      super().__init__()
      return
      if num_virtual_bits == None:
        self.num_virtual_bits = random.randint(self.MIN_VIRTUAL_ADDRESS_BITS, self.MAX_VIRTUAL_ADDRESS_BITS)
      
      self.offset = random.randint(0, 2**(self.num_virtual_bits-2))
      self.segment = random.choices([0,1,2,4], weights=[(1-self.PROBABILITY_OF_INVALID)/3, (1-self.PROBABILITY_OF_INVALID)/3, self.PROBABILITY_OF_INVALID, (1-self.PROBABILITY_OF_INVALID)/3])
      
      self.virtual_address = self.segment * 2**(self.num_virtual_bits-2) + self.offset
      
      # Generate the segment base and bounds randomly
      if self.segment == 3:
        # Then we're invalid, and that's a different can of worms
        # todo
        pass
      # todo complete this after I do explanations

def main():
  pass

if __name__ == "__name__":
  pass