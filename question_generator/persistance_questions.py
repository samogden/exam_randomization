#!env python

import random
import math
from typing import List

from .question import Question, CanvasQuestion
from .variable import Variable, VariableBytes, VariableFloat

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class HardDriveAccessTime(CanvasQuestion):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    
    # Given:
    # 1. hard drive rotation speed
    # 2. seek time
    # 3. transfer rate
    # 4. number of reads
    # 5. size of reads
    
    # Calculate
    # 1. rotational delay
    # 2. access time
    # 3. transfer time
    # 4. disk access time
    
    self.hard_drive_rotation_speed = 100 * random.randint(36, 150) # e.g. 3600rpm to 15000rpm
    self.seek_delay = float(round(random.randrange(3, 20), 2))
    self.transfer_rate = random.randint(50, 300)
    self.number_of_reads = random.randint(1, 20)
    self.size_of_reads = random.randint(1, 10)
    
    self.rotational_delay = (1 / self.hard_drive_rotation_speed) * (60 / 1) *  (1000 / 1) * (1/2)
    self.access_delay = self.rotational_delay + self.seek_delay
    self.transfer_delay = 1000 * (self.size_of_reads * self.number_of_reads) / 1024 / self.transfer_rate
    self.disk_access_delay = self.access_delay * self.number_of_reads + self.transfer_delay
    
    self.rotational_delay_var = VariableFloat("Rotational Delay", self.rotational_delay)
    self.access_delay_var = VariableFloat("Access Delay", self.access_delay)
    self.transfer_delay_var = VariableFloat("Transfer Delay", self.transfer_delay)
    self.disk_access_delay_var = VariableFloat("Disk Access Delay", self.disk_access_delay)
    
    log.debug(f"self.rotational_delay: {self.rotational_delay}")
    log.debug(f"self.access_delay: {self.access_delay}")
    log.debug(f"self.transfer_delay: {self.transfer_delay}")
    log.debug(f"self.disk_access_delay: {self.disk_access_delay}")
    
    
    self.blank_vars.update({
      "rotational_delay" : self.rotational_delay_var,
      "access_delay" : self.access_delay_var,
      "transfer_delay" : self.transfer_delay_var,
      "disk_access_delay" : self.disk_access_delay_var,
    })
    
  
  def get_question_body(self, *args, **kwargs) -> List[str]:
    lines = [
      "Given the information below, please calculate the following values.  Make sure your answers are rounded to 2 decimal points (even if they are whole numbers)."
      ]
    
    
    lines.extend(
      self.get_table_lines(
        table_data={
          f"Hard Drive Rotation Speed" : [f"{self.hard_drive_rotation_speed}RPM"],
          f"Seek Delay" : [f"{self.seek_delay}ms"],
          f"Transfer Rate" : [f"{self.transfer_rate}MB/s"],
          f"Number of Reads" : [f"{self.number_of_reads}"],
          f"Size of Reads" : [f"{self.size_of_reads}KB"],
        },
        add_header_space=True
      )
    )
    
    
    lines.extend(
      self.get_table_lines(
        headers=["Variable", "Value"],
        table_data={
          "Rotational Delay": ["[rotational_delay]ms"],
          "Access Delay" : ["[access_delay]ms"],
          "Transfer Delay" : ["[transfer_delay]ms"],
          "Total Disk Access Delay" : ["[disk_access_delay]ms"]
        },
        sorted_keys=["Rotational Delay", "Access Delay", "Transfer Delay", "Total Disk Access Delay"]
      )
    )
    
    return lines
  
  def get_explanation(self, *args, **kwargs) -> List[str]:
    lines = [
      "To calculate the total disk access time (or \"delay\"), we should first calculate each of the individual parts.",
      r"Since we know that \( t_{total} = (\text{# of reads}) \cdot t_{access} + t_{transfer} \)"
      r"we therefore need to calculate \(t_{access}\) and  \(t_{transfer}\), where "
      r"\(t_{access} = t_{rotation} + t_{seek} \).",
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
      r"Next we need to calculate our transfer delay, \(t_{transfer}\), which we do as:",
      "$$ " + f"t_{{transfer}} = \\frac{{{self.number_of_reads} \\cdot {self.size_of_reads}KB}}{{1}} \\cdot \\frac{{1MB}}{{1024KB}} \\cdot \\frac{{1 second}}{{{self.transfer_rate}MB}} \\cdot \\frac{{1000ms}}{{1second}} = {self.transfer_delay:0.2}ms" + " $$",
      ""
    ])
    
    lines.extend([
      "Putting these together we see:",
      "$$ " + f"t_{{total}} = (# reads) \\cdot t_{{access}} + t_{{transfer}} = {self.number_of_reads} \cdot {self.access_delay:0.2f} + {self.transfer_delay:0.2f} = {self.disk_access_delay:0.2f}ms" + " $$"
    ])
    return lines
  
