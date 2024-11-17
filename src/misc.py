#!env python

import enum

class OutputFormat(enum.Enum):
  LATEX = enum.auto(),
  CANVAS = enum.auto()