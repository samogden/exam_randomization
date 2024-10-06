#!env python
import pprint
from typing import List, Dict

from .question import Question, CanvasQuestion
from .variable import Variable, VariableHex

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
  PROBABILITY_OF_VALID = .875
  
  def get_question_prelude(self) -> List[str]:
    prelude = super().get_question_prelude()
    prelude.extend([
      "If the memory access is invalid, simply write INVALID"
    ])
    return prelude

class BaseAndBounds(MemoryAccessQuestion):
  MAX_BITS = 32
  MAX_BOUNDS_BITS = 16
  
  def __init__(
      self
  ):
    
    use_binary = random.randint(0,1) % 2 ==0
    
    bounds_bits = random.randint(1, self.MAX_BOUNDS_BITS)
    base_bits = self.MAX_BITS - bounds_bits
    
    self.bounds = int(math.pow(2, bounds_bits))
    self.base = random.randint(1, int(math.pow(2, base_bits))) * self.bounds
    self.virtual_address = random.randint(1, int(self.bounds / self.PROBABILITY_OF_VALID))
    
    self.bounds_var = VariableHex("Bounds", self.bounds, default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX))
    self.base_var = VariableHex("Base", self.base, default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX))
    self.virtual_address_var = VariableHex("Virtual Address", self.virtual_address, default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX))
    
    logging.debug(f"bounds: {self.bounds}")
    logging.debug(f"base: {self.base}")
    logging.debug(f"va: {self.virtual_address}")
    
    if self.virtual_address < self.bounds:
      self.physical_address_var = VariableHex(
        "Physical Address",
        num_bits=math.ceil(math.log2(self.base + self.virtual_address)),
        true_value=(self.virtual_address + self.base),
        default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX)
      )
    else:
      self.physical_address_var = Variable("Physical Address", "INVALID")
    
    logging.debug(f"pa: {self.virtual_address + self.base}")
    logging.debug(f"pa: {self.physical_address_var}")
    
    
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
    
    self.virtual_address_var = VariableHex("Virtual Address", self.virtual_address, num_bits=(self.num_vpn_bits+self.num_offset_bits), default_presentation=VariableHex.PRESENTATION.BINARY)
    self.vpn_var = VariableHex("VPN", self.vpn, num_bits=self.num_vpn_bits, default_presentation=VariableHex.PRESENTATION.BINARY)
    
    if random.choices([True, False], weights=[(1-self.PROBABILITY_OF_VALID), self.PROBABILITY_OF_VALID], k=1)[0]:
      # Set our actual entry to be in the table and valid
      self.pte = self.pfn + (2**(self.num_pfn_bits))
      self.physical_address_var = VariableHex("Physical Address", self.physical_address, num_bits=(self.num_pfn_bits+self.num_offset_bits), default_presentation=VariableHex.PRESENTATION.BINARY)
      self.pfn_var = VariableHex("PFN", self.pfn, num_bits=self.num_pfn_bits, default_presentation=VariableHex.PRESENTATION.BINARY)
    else:
      # Leave it as invalid
      self.pte = self.pfn
      self.physical_address_var = Variable("Physical Address", "INVALID")
      self.pfn_var = Variable("PFN",  "INVALID")
    
    self.pte_var = VariableHex("PTE", self.pte, num_bits=(self.num_pfn_bits+1), default_presentation=VariableHex.PRESENTATION.BINARY)
    
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
        # self.pfn_var,
        self.pte_var,
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
    try:
      self.given_vars.remove(self.pfn_var)
    except ValueError:
      pass
  
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
        if random.choices([True, False], weights=[(1-self.PROBABILITY_OF_VALID), self.PROBABILITY_OF_VALID], k=1)[0]:
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


######################
## Canvas Questions ##
######################

  
  def get_explanation(self, *args, **kwargs) -> List[str]:
    
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


class BaseAndBounds_canvas(BaseAndBounds, CanvasQuestion):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    self.blank_vars.update({
      "physical_address_val": self.physical_address_var
    })
  
  def get_question_body(self, *args, **kwargs) -> List[str]:
    question_lines = [
      f"Given a virtual address space with the below base and bounds, what is the physical address of {self.virtual_address_var}?",
      "If it is not a valid address simply enter INVALID."
    ]
    question_lines.extend(
      self.get_table_lines(
        table_data={
          "Base" : [self.base_var],
          "Bounds" : [self.bounds_var]
        },
        sorted_keys=[
          "Base", "Bounds"
        ],
        add_header_space=False
      )
    )
    
    question_lines.extend([
      "Physical Address: [physical_address_val]",
    ])
    
    return question_lines
    
  
  def get_explanation(self, *args, **kwargs) -> List[str]:
    explanation_lines = [
      "There's two steps to figuring out base and bounds.",
      "1. Are we within the bounds?",
      "2. If so, add to our base.",
      "",
    ]
    if self.virtual_address < self.bounds:
      explanation_lines.extend([
        f"Step 1: {self.virtual_address_var.true_value} < {self.bounds_var.true_value} --> {'<b>>VALID</b>' if (self.virtual_address < self.bounds) else 'INVALID'}",
        "",
        f"Step 2: Since the previous check passed, we calculate {self.base_var.true_value} + {self.virtual_address_var.true_value} = <b>{self.physical_address_var.true_value}</b>.",
        "If it had been invalid we would have simply written INVALID"
      ]
      )
    else:
      explanation_lines.extend([
        f"Step 1: {self.virtual_address_var.true_value} < {self.bounds_var.true_value} --> {'VALID' if (self.virtual_address < self.bounds) else '<b>INVALID</b>'}",
        "",
        f"Step 2: Since the previous check failed, we simply write <b>INVALID</b>.",
        f"If it had been valid, we would have calculated {self.base_var.true_value} + {self.virtual_address_var.true_value} = {self.physical_address_var.true_value}"
      ]
      )
    return explanation_lines


class Segmentation_canvas(MemoryAccessQuestion, CanvasQuestion):
  MAX_BITS = 32
  MIN_VIRTUAL_BITS = 4
  MAX_VIRTUAL_BITS = 10
  def __init__(self, *args, **kwargs):
    super().__init__(given_vars=[], target_vars=[], *args, **kwargs)
    
    use_binary = random.randint(0,1) % 2 ==0
    
    self.base = {
      "code" : 0,
      "heap" : 0,
      "stack" : 0,
    }
    self.bounds = {
      "code" : 0,
      "heap" : 0,
      "stack" : 0,
    }
    
    self.virtual_bits = random.randint(self.MIN_VIRTUAL_BITS, self.MAX_VIRTUAL_BITS)
    self.physical_bits = random.randint(self.virtual_bits+1, self.MAX_BITS)
    
    max_bounds = 2**(self.virtual_bits - 3)
    
    def segment_collision(base, bounds):
      # lol, I think this is probably silly, but should work
      return 0 != len(set.intersection(*[
        set(range(base[segment], base[segment]+bounds[segment]+1))
        for segment in base.keys()
      ]))
      
      
    while (segment_collision(self.base, self.bounds)):
      for segment in self.base.keys():
        self.bounds[segment] = random.randint(1, max_bounds)
        self.base[segment] = random.randint(0, (2**self.physical_bits - self.bounds[segment]))
    
    self.segment = random.choice(list(self.base.keys()) + ["unallocated"])
    self.segment_bits = {
      "code" : 0,
      "heap" : 1,
      "unallocated" : 2,
      "stack" : 3
    }[self.segment]
    
    try:
      self.virtual_address_offset = random.randint(0,
        min([
          ((self.virtual_bits-2)**2)-1,
          int(self.bounds[self.segment] / self.PROBABILITY_OF_VALID)
        ])
      )
    except KeyError:
      self.virtual_address_offset = random.randint(0, ((self.virtual_bits-2)**2)-1)
      
    self.virtual_address = (
        (self.segment_bits << (self.virtual_bits - 2))
        + self.virtual_address_offset
    )
    
    if self.segment == "unallocated" or (self.bounds[self.segment] < self.virtual_address_offset):
      self.physical_address_var = Variable("Physical Address", "INVALID")
    else:
      if not self.__within_bounds(self.segment, self.virtual_address_offset, self.bounds[self.segment]):
        self.physical_address_var = Variable("Physical Address", "INVALID")
      else:
        
        if self.segment in ["code", "heap"]:
          self.physical_address_var = VariableHex("Physical Address", true_value=self.base[self.segment] + self.virtual_address_offset, num_bits=self.physical_bits, default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX))
        else:
          neg_offset = self.virtual_address_offset - 2**(self.virtual_bits-2)
          self.physical_address_var = VariableHex("Physical Address", true_value=self.base[self.segment] + neg_offset, num_bits=self.physical_bits, default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX))
          
      
    self.virtual_address_var = VariableHex("Virtual Address", true_value=self.virtual_address, default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX))
    self.segment_var = Variable("Segment", true_value=self.segment, default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX))
    self.base_vars = {
      "code" : VariableHex("Code Base", true_value=self.base["code"], default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX)),
      "heap" : VariableHex("Heap Base", true_value=self.base["heap"], default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX)),
      "stack" : VariableHex("Stack Base", true_value=self.base["stack"], default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX)),
    }
    
    self.bounds_vars = {
      "code" : VariableHex("Code Bound", true_value=self.bounds["code"], default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX)),
      "heap" : VariableHex("Heap Bound", true_value=self.bounds["heap"], default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX)),
      "stack" : VariableHex("Stack Bound", true_value=self.bounds["stack"], default_presentation=(VariableHex.PRESENTATION.BINARY if use_binary else VariableHex.PRESENTATION.HEX)),
    }
    
    self.blank_vars.update({
      "segment_val" : self.segment_var,
      "physical_address_val" : self.physical_address_var
    })
  
  def get_question_body(self) -> List[str]:
    question_lines = [
      f"Given a virtual address space of {self.virtual_bits}bits, and a physical address space of {self.physical_bits}bits, what is the physical address associated with the virtual address {self.virtual_address_var}?",
      "If it is invalid simply type INVALID"
    ]
    
    question_lines.extend(
      self.get_table_lines(
        table_data={
          "code": [self.base_vars["code"], self.bounds_vars["code"]],
          "heap": [self.base_vars["heap"], self.bounds_vars["heap"]],
          "stack": [self.base_vars["stack"], self.bounds_vars["stack"]],
        },
        sorted_keys=[
          "code", "heap", "stack"
        ],
        headers=["base", "bounds"],
        add_header_space=True
      )
    )
    
    question_lines.extend([
      "Segment name: [segment_val]",
      "Physical Address: [physical_address_val]"
    ])
    
    return question_lines
  
  def __within_bounds(self, segment, offset, bounds):
    if segment == "unallocated":
      return False
    elif segment == "stack":
      neg_offset = offset - 2**(self.virtual_bits-2)
      if bounds < abs(neg_offset):
        return False
      else:
        return True
    else:
      # Then we are in the code or the heap
      if bounds < offset:
        return False
      else:
        return True
  
  def get_explanation(self, *args, **kwargs) -> List[str]:
    explanation_lines = [
      "The core idea to keep in mind with segmentation is that you should always check the first two bits of the virtual address to see what segment it is in and then go from there."
      "Keep in mind, we also may need to include padding if our virtual address has a number of leading zeros left off!",
      ""
    ]
    
    explanation_lines.extend([
      f"In this problem our virtual address, converted to binary and including padding, is 0b{self.virtual_address:0{self.virtual_bits}b}.",
      f"From this we know that our segment bits are 0b{self.segment_bits:2b}, meaning that we are in the <b>{self.segment_var}</b> segment.",
      ""
    ])
    
    if self.segment == "unallocated":
      explanation_lines.extend([
        "Since this is the unallocated segment there are no possible valid translations, so we enter <b>INVALID</b>."
      ])
    else:
      explanation_lines.extend([
        f"Since we are in the {self.segment_var} segment, we see from our table that our bounds are {self.bounds_vars[self.segment]}. "
        f"Remember that our check for our {self.segment_var} segment is: "
      ])
      
      if self.segment == "stack":
        explanation_lines.extend([
          "abs(offset – MAX_SEGMENT_SIZE) <= bounds(stack)",
          f"Where MAX_SEGMENT_SIZE is {2**(self.virtual_bits-2)} since our virtual address size is defined by {self.virtual_bits} bits.",
          "This becomes:",
          f"<code> if (abs(0b{self.virtual_address_offset:0b} - 0b{2**(self.virtual_bits-2):0b}) > 0b{self.bounds[self.segment]:0b}) : INVALID</code>",
          "which becomes",
          f"<code> if (abs(-0b{abs(self.virtual_address_offset - 2**(self.virtual_bits-2)):0b}) > 0b{self.bounds[self.segment]:0b} : INVALID</code>",
          "which becomes",
          f"<code> if (0b{abs(self.virtual_address_offset - 2**(self.virtual_bits-2)):0b}) > 0b{self.bounds[self.segment]:0b} : INVALID</code>",
        ])
      else:
        explanation_lines.extend([
          f"<code> if (offset > bounds({self.segment})) : INVALID</code>",
          "which becomes"
          f"<code> if ({self.virtual_address_offset:0b} > {self.bounds[self.segment]:0b}) : INVALID</code>"
        ])
        
      if not self.__within_bounds(self.segment, self.virtual_address_offset, self.bounds[self.segment]):
        # then we are outside of bounds
        explanation_lines.extend([
          "We can therefore see that we are outside of bounds so we should put <b>INVALID</b>.",
          "If we <i>were</i> requesting a valid memory location we could use the below steps to do so."
        ])
      else:
        explanation_lines.extend([
          "We are therefore in bounds so we can calculate our physical address."
        ])
      
      explanation_lines.append("")
      
      explanation_lines.extend([
        "To find the physical address we use the formula:"
      ])
      if self.segment == "stack":
        explanation_lines.extend([
          "<code>physical_address = offset + (offset – MAX_SEGMENT_SIZE)<code>",
          "which becomes",
          "<code>physical_address = offset + (offset – MAX_SEGMENT_SIZE)<code>",
        ])
      
      
      
    return explanation_lines
    


class Paging_canvas(Paging_with_table, CanvasQuestion):
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    self.blank_vars.update({
      "vpn_val" : self.vpn_var,
      "pte_val" : self.pte_var,
      "pfn_val" : self.pfn_var,
      "physical_address_val": self.physical_address_var
    })
  
  def get_question_body(self, *args, **kwargs) -> List[str]:
    # markdown_lines = super().get_question_body()
    markdown_lines = [
      "Given the below information please calculate the equivalent physical address of the given virtual address, filling out all steps along the way."
    ]
    
    markdown_lines.extend(
      self.get_table_lines(
        table_data={
          "Virtual Address": [self.virtual_address_var],
          "# VPN bits": [self.vpn_bits_var],
          "# PFN bits": [self.pfn_bits_var],
        },
        sorted_keys=[
          "Virtual Address",
          "# VPN bits",
          "# PFN bits",
        ],
        add_header_space=False
      )
    )
    
    # Make values for Page Table
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
        if random.choices([True, False], weights=[(1-self.PROBABILITY_OF_VALID), self.PROBABILITY_OF_VALID], k=1)[0]:
          # Randomly set it to be valid
          pte += (2**(self.num_pfn_bits))
      # Once we have a unique random entry, put it into the Page Table
      page_table[vpn] = pte
    
    table_lines = self.get_table_lines(
      table_data={
        # pte: [f"<tt>0b{vpn:0{self.num_vpn_bits}b}</tt>"]
        f"<tt>0b{vpn:0{self.num_vpn_bits}b}</tt>" : [f"<tt>0b{pte:0{(self.num_pfn_bits+1)}b}</tt>"]
        for vpn, pte in sorted(page_table.items())
      },
      # sorted_keys=[
      #   sorted(page_table.keys())
      # ],
      headers=["VPN", "PTE"]
    )
    
    markdown_lines.extend(table_lines)
    
    markdown_lines.extend([
      "VPN: [vpn_val]",
      "PTE: [pte_val]",
      "PFN: [pfn_val]",
      "Physical Address: [physical_address_val]",
    ])
    
    return markdown_lines
  
  
  def get_explanation(self, *args, **kwargs) -> List[str]:
    explanation_lines = [
      "The core idea of Paging is we want to break the virtual address into the VPN and the offset.  "
      "From here, we get the Page Table Entry corresponding to the VPN, and check the validity of the entry.  "
      "If it is valid, we clear the metadata and attach the PFN to the offset and have our physical address.",
      "",
      "Don't forget to pad with the appropriate number of 0s (the appropriate number is the number of bits)!",
      "",
      f"Virtual Address = VPN | offset",
      f"<tt>0b{self.virtual_address:0{self.num_vpn_bits+self.num_offset_bits}b}</tt> = <tt>0b{self.vpn:0{self.num_vpn_bits}b}</tt> | <tt>0b{self.offset:0{self.num_offset_bits}b}</tt>",
      ""
    ]
    
    explanation_lines.extend([
      "We next use our VPN to index into our page table and find the corresponding entry."
      f"Our Page Table Entry is:",
      "",
      f"<tt>0b{self.pte:0{(self.num_pfn_bits+1)}b}</tt>"
      f"which we found by looking for our VPN in the page table.",
      "",
    ])
    
    is_valid = (self.pte // (2**self.num_pfn_bits) == 1)
    if is_valid:
      explanation_lines.extend([
        f"In our PTE we see that the first bit is <b>{self.pte // (2**self.num_pfn_bits)}</b> meaning that the translation is <b>VALID</b>"
      ])
    else:
      explanation_lines.extend([
        f"In our PTE we see that the first bit is <b>{self.pte // (2**self.num_pfn_bits)}</b> meaning that the translation is <b>INVALID</b>.",
        "Therefore, we just write \"INVALID\" as our answer.",
        "If it were valid we would complete the below steps.",
        "",
        "<hr>"
        "\n",
      ])
    
    explanation_lines.extend([
      "Next, we convert our PTE to our PFN by removing our metadata.  In this case we're just removing the leading bit.  We can do this by applying a binary mask.",
      f"PFN = PTE & mask",
      f"which is,",
      "",
      f"<tt>{self.pfn_var}</tt> = <tt>0b{self.pte:0{self.num_pfn_bits+1}b}</tt> & <tt>0b{(2**self.num_pfn_bits)-1:0{self.num_pfn_bits+1}b}</tt>"
    ])
    
    explanation_lines.extend([
      "We then add combine our PFN and offset",
      "",
      "Physical Address = PFN | offset",
      f"{'<tt><b>' if is_valid else ''}0b{self.physical_address:0{self.num_pfn_bits+self.num_offset_bits}b}{'</b></tt>' if is_valid else ''} = <tt>0b{self.pfn:0{self.num_pfn_bits}b}</tt> | <tt>0b{self.offset:0{self.num_vpn_bits}b}</tt>",
      "",
      "",
      "Note: Strictly speaking, this calculation is:",
      f"{'<tt><b>' if is_valid else ''}0b{self.physical_address:0{self.num_pfn_bits+self.num_offset_bits}b}{'</b></tt>' if is_valid else ''} = <tt>0b{self.pfn:0{self.num_pfn_bits}b}{0:0{self.num_offset_bits}}</tt> + <tt>0b{self.offset:0{self.num_offset_bits}b}</tt>",
      "But that's a lot of extra 0s, so I'm splitting them up for succinctness",
      ""
    ])
    return explanation_lines


def main():
  pass

if __name__ == "__name__":
  pass