#!env python
from __future__ import annotations

import enum
from typing import List, Dict
import random
import re

import lark

from question import QuestionRegistry, Question, Answer

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class BNF:
  
  class Grammar:
    def __init__(self, symbols, start_symbol=None):
      self.start_symbol = start_symbol if start_symbol is not None else symbols[0]
      self.symbols = symbols
  
    def generate(self):
      curr_symbols : List[BNF.Symbol] = [self.start_symbol]
      # Check to see if we have any non-terminals left
      while any(map(lambda s: s.kind == BNF.Symbol.Kind.NonTerminal, curr_symbols)):
        
        log.debug(f"curr_symbols: {' '.join([str(s) for s in curr_symbols])}")
        
        # Walk through the current symbols and build a new list of symbols from it
        next_symbols : List[BNF.Symbol] = []
        for symbol in curr_symbols:
          next_symbols.extend(symbol.expand())
        curr_symbols = next_symbols
      # Take all the current symbols and combine them
      return ''.join([str(s) for s in curr_symbols])
    
    def print(self):
      for symbol in self.symbols:
        print(symbol.get_full_str())
      
  
  class Symbol:
    
    class Kind(enum.Enum):
      NonTerminal = enum.auto()
      Terminal = enum.auto()
      
    def __init__(self, symbol : str, kind : Kind):
      self.symbol = symbol
      self.kind = kind
      self.productions : List[BNF.Production] = [] # productions
    
    def __str__(self):
      return f"{self.symbol}"
    
    def get_full_str(self):
      return f"{self.symbol} ::= {' | '.join([str(p) for p in self.productions])}"
    
    def add_production(self, production: BNF.Production):
      self.productions.append(production)
    
    def expand(self) -> List[BNF.Symbol]:
      if self.kind == BNF.Symbol.Kind.Terminal:
        return [self]
      return random.choice(self.productions).production
  
  class Production:
    def __init__(self, production_line, nonterminal_symbols: Dict[str, BNF.Symbol]):
      self.production = [
        (nonterminal_symbols.get(symbol, BNF.Symbol(symbol, BNF.Symbol.Kind.Terminal)))
        for symbol in production_line.split(' ')
      ]
      
    def __str__(self):
      return f"{' '.join([str(s) for s in self.production])}"
  
  
  @staticmethod
  def parse_bnf(grammar_str) -> BNF.Grammar:
    
    # Figure out all the nonterminals and create a Token for them
    terminal_symbols = {}
    start_symbol = None
    for line in grammar_str.strip().splitlines():
      if "::=" in line:
        non_terminal_str, _ = line.split("::=", 1)
        non_terminal_str = non_terminal_str.strip()
        
        terminal_symbols[non_terminal_str] = BNF.Symbol(non_terminal_str, BNF.Symbol.Kind.NonTerminal)
        if start_symbol is None:
          start_symbol = terminal_symbols[non_terminal_str]
    
    # Parse the grammar statement
    for line in grammar_str.strip().splitlines():
      if "::=" in line:
        # Split the line into non-terminal and its expansions
        non_terminal_str, expansions = line.split("::=", 1)
        non_terminal_str = non_terminal_str.strip()
        
        non_terminal = terminal_symbols[non_terminal_str]
        
        for production_str in expansions.split('|'):
          production_str = production_str.strip()
          non_terminal.add_production(BNF.Production(production_str, terminal_symbols))
    bnf_grammar = BNF.Grammar(list(terminal_symbols.values()), start_symbol)
    return bnf_grammar


@QuestionRegistry.register()
class LanguageQuestion:
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    self.grammar_str = """
      <expression> ::= <term> | <expression> "+" <term> | <expression> "-" <term>
      <term>       ::= <factor> | <term> "*" <factor> | <term> "/" <factor>
      <factor>     ::= <number> | "(" <expression> ")"
      <number>     ::= <digit> | <number> <digit>
      <digit>      ::= "0" | "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
      """
    
    self.instantiate()
  
  def instantiate(self, *args, **kwargs):
    self.answers = []
    
    self.answers.extend([
    
    ])
  
  def get_body_lines(self, *args, **kwargs) -> List[str]:
    lines = []
    return lines
  
  def get_explanation_lines(self, *args, **kwargs) -> List[str]:
    lines = []
    return lines
