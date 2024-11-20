#!env python
from __future__ import annotations

import enum
import pprint
import re
from typing import List, Tuple, Dict, Type, Any

import pypandoc

from src.misc import OutputFormat
from src.question import Question, Answer, TableGenerator

import random
import math
import collections

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)



class HardDriveAccessTime(Question):
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    self.instantiate()
  
  def instantiate(self):
    super().instantiate()
    
    
    self.hard_drive_rotation_speed = 100 * random.randint(36, 150) # e.g. 3600rpm to 15000rpm
    self.seek_delay = float(round(random.randrange(3, 20), 2))
    self.transfer_rate = random.randint(50, 300)
    self.number_of_reads = random.randint(1, 20)
    self.size_of_reads = random.randint(1, 10)
    
    self.rotational_delay = (1 / self.hard_drive_rotation_speed) * (60 / 1) *  (1000 / 1) * (1/2)
    self.access_delay = self.rotational_delay + self.seek_delay
    self.transfer_delay = 1000 * (self.size_of_reads * self.number_of_reads) / 1024 / self.transfer_rate
    self.disk_access_delay = self.access_delay * self.number_of_reads + self.transfer_delay
    
    self.answers.extend([
      Answer("answer__rotational_delay", self.rotational_delay),
      Answer("answer__access_delay", self.access_delay),
      Answer("answer__transfer_delay", self.transfer_delay),
      Answer("answer__disk_access_delay", self.disk_access_delay),
    ])
  
  def get_body_lines(self, *args, **kwargs) -> List[str]:
    lines = [
      "Given the information below, please calculate the following values.  Make sure your answers are rounded to 2 decimal points (even if they are whole numbers), and do so after you finish all your calculations! (i.e. don't use your rounded answers to calculate your overall answer)"
    ]
    
    lines.extend([
      TableGenerator(
        value_matrix=[
          [f"Hard Drive Rotation Speed", f"{self.hard_drive_rotation_speed}RPM"],
          [f"Seek Delay", f"{self.seek_delay}ms"],
          [f"Transfer Rate", f"{self.transfer_rate}MB/s"],
          [f"Number of Reads", f"{self.number_of_reads}"],
          [f"Size of Reads", f"{self.size_of_reads}KB"],
        ]
      )
    ])
    
    lines.extend(
      self.get_table_generator(
        headers=["Variable", "Value"],
        table_data={
          "Rotational Delay": ["[answer__rotational_delay]ms"],
          "Access Delay" : ["[answer__access_delay]ms"],
          "Transfer Delay" : ["[answer__transfer_delay]ms"],
          "Total Disk Access Delay" : ["[answer__disk_access_delay]ms"]
        },
        sorted_keys=["Rotational Delay", "Access Delay", "Transfer Delay", "Total Disk Access Delay"]
      )
    )
    
    return lines
  
  def get_explanation_lines(self, *args, **kwargs) -> List[str]:
    lines = [
      "To calculate the total disk access time (or \"delay\"), we should first calculate each of the individual parts.",
      r"Since we know that  $t_{total} = (\text{# of reads}) \cdot t_{access} + t_{transfer}$"
      r"we therefore need to calculate $t_{access}$ and  $t_{transfer}$, where "
      r"$t_{access} = t_{rotation} + t_{seek}$.",
      "",
    ]
    
    lines.extend([
      "Starting with the rotation delay, we calculate:",
      "$$ t_{rotation} = " + f"\\frac{{1 minute}}{{{self.hard_drive_rotation_speed}revolutions}}"  + r"\cdot \frac{60 seconds}{1 minute} \cdot \frac{1000 ms}{1 second} \cdot \frac{1 revolution}{2} = " + f"{self.rotational_delay:0.2f}ms" + "$$",
      ""
    ])
    lines.extend([
      "Now we can calculate:",
      f"$$ t_{{access}} = t_{{rotation}} + t_{{seek}} = {self.rotational_delay:0.2f}ms + {self.seek_delay:0.2f}ms = {self.access_delay:0.2f}ms $$",
      ""
    ])
    
    lines.extend([
      r"Next we need to calculate our transfer delay, $t_{transfer}$, which we do as:",
      "$$" + f"t_{{transfer}} = \\frac{{{self.number_of_reads} \\cdot {self.size_of_reads}KB}}{{1}} \\cdot \\frac{{1MB}}{{1024KB}} \\cdot \\frac{{1 second}}{{{self.transfer_rate}MB}} \\cdot \\frac{{1000ms}}{{1second}} = {self.transfer_delay:0.2}ms" + "$$",
      ""
    ])
    
    lines.extend([
      "Putting these together we see:",
      "",
      "$$" + f"t_{{total}} = (# reads) \\cdot t_{{access}} + t_{{transfer}} = {self.number_of_reads} \\cdot {self.access_delay:0.2f} + {self.transfer_delay:0.2f} = {self.disk_access_delay:0.2f}ms" + "$$"
    ])
    return lines




class INodeAccesses(Question):
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    self.instantiate()
  
  def instantiate(self):
    super().instantiate()
    
    self.block_size = 1024 * random.randint(1,10)
    self.inode_number = random.randint(0,1024)
    self.inode_start_location = self.block_size * random.randint(2, 5)
    self.inode_size = 2**random.randint(6, int(math.log2(self.block_size)-2))
    
    self.inode_address = self.inode_start_location + self.inode_number * self.inode_size
    self.inode_block = self.inode_address // self.block_size
    self.inode_address_in_block = self.inode_address % self.block_size
    self.inode_index_in_block = int(self.inode_address_in_block / self.inode_size)
    
    
    self.answers.extend([
      Answer("answer__inode_address", self.inode_address),
      Answer("answer__inode_block", self.inode_block),
      Answer("answer__inode_address_in_block", self.inode_address_in_block),
      Answer("answer__inode_index_in_block", self.inode_index_in_block),
    ])
  
  def get_body_lines(self, *args, **kwargs) -> List[str]:
    lines = [
      "Given the information below, please calculate the following values. (hint: they should all be round numbers)."
    ]
    
    lines.extend(
      self.get_table_generator(
        table_data={
          f"Block Size" : [f"{self.block_size} Bytes"],
          f"Inode Number" : [f"{self.inode_number}"],
          f"Inode Start Location" : [f"{self.inode_start_location} Bytes"],
          f"Inode size" : [f"{self.inode_size} Bytes"],
        },
        add_header_space=True
      )
    )
    
    lines.extend(
      self.get_table_generator(
        headers=["Variable", "Value"],
        table_data={
          "Inode address": ["[answer__inode_address] Bytes"],
          "Block containing inode" : ["[answer__inode_block]"],
          "Inode address (offset) within block" : ["[answer__inode_address_in_block] Bytes offset"],
          "Inode index within block" : ["[answer__inode_index_in_block]"]
        },
        sorted_keys=["Inode address", "Block containing inode", "Inode address (offset) within block", "Inode index within block"]
      )
    )
    
    return lines
  
  def get_explanation_lines(self, *args, **kwargs) -> List[str]:
    lines = []
    
    lines.extend([
      "If we are given an inode number, there are a few steps that we need to take to load the actual inode.  These consist of determining the address of the inode, which block would contain it, and then its address within the block.",
      ""
      "To find the inode address, we calculate:",
      r"$${addr}_{inode} = {addr}_{inode\_start} + (\text{inode#}) \cdot (\text{inode size}) = " + f"{self.inode_start_location} + {self.inode_number} \\cdot {self.inode_size} = {self.inode_address}" + "$$",
      "",
      "Next, we us this to figure out what block the inode is in.  We do this directly so we know what block to load, thus minimizing the number of loads we have to make."
      r"$$ \text{block_to_load} = {addr}_{inode} \mathbin{//} (\text{block size}) = " + f"{self.inode_address} \\mathbin{{//}} {self.block_size} = {self.inode_block}" + "$$",
      "",
      "When we load this block, we now have in our system memory (remember, blocks on the hard drive are effectively useless to us until they're in main memory!), the inode, so next we need to figure out where it is within that block."
      "This means that we'll need to find the offset into this block.  We'll calculate this both as the offset in bytes, and also in number of inodes, since we can use array indexing.",
      "",
      r"$$\text{offset within block} = {addr}_{inode} \% (\text{block size}) = " + f"{self.inode_address} % {self.block_size} = {self.inode_address_in_block} Bytes offset" + "$$",
      "\nand\n"
      r"$$ \text{index within block} = \frac{\text{offset within block}}{\text{inode size}} = " + f"\\frac{{{self.inode_address_in_block}}}{{{self.inode_size}}} = {self.inode_index_in_block}" + "$$"
    ])
    
    return lines
  