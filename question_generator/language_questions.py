#env python
from __future__ import annotations
import random
import string
from typing import Dict, List, Iterable, Tuple

import question
import variable

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


class BNF_from_text:
  def __init__(self):
    super().__init__()
    self.productions : List[BNF_from_text.Production] = []
  
  def add_production(self, p : Production):
    if p not in self.productions:
      self.productions.append(p)
  
  @classmethod
  def create_bnf(cls, bnf_str: str):
    bnf_rule_lines = bnf_str.split('\n') # Break it up so we have a list of all of the different strings, which will help later
    log.debug(f"bnf_rule_lines: {bnf_rule_lines}")
    
    bnf_pairs = [
      BNF_from_text.NonTerminal(
        l.split('::=')[0].strip(),
        [p.strip() for p in l.split('::=')[1].strip().split('|')]
      )
      for l in bnf_rule_lines if l.strip() != ""
    ]
    log.debug(f"bnf_nonterminal_tokens: {bnf_pairs}")
    

  class NonTerminal:
    def __init__(self, non_terminal_token : str, productions : List[str]):
      self.token = non_terminal_token
      self.productions_unparsed = productions
      self.productions = None # We will need to parse out the tokens that belong to other non-terminals
    
    def parse_productions(self, list_of_nonterminals : List[BNF_from_text.NonTerminal]):
      
      def insert_nonterminal(current_production : str, nonterminal : BNF_from_text.NonTerminal) -> List[str]: # todo: check to make sure it isn't the _first_ thing
        if nonterminal.token not in current_production:
          return [current_production]
        output_production = []
        for p in current_production.split(nonterminal.token):
          output_production.append(p)
          output_production.append(nonterminal)
        return output_production[:-1] # Slice off the last nonterminal we put in
      
      # Note that the order of these matters since I'm not using a placeholder
      for production in self.productions_unparsed:
        production = [production]
        # We want to check each
        
        
        for nonterminal in list_of_nonterminals:
          # The goal is that every time the non-terminal comes up we break into two strings and put the non-terminal between them
          for subproduction in production:
            if isinstance(subproduction,  BNF_from_text.NonTerminal): continue
            if nonterminal.token in production:
              pass
              # Then we want to split on it and add each piece back to the productions
      pass
      
  
  class Terminal:
    pass
  
  class Production:
    pass
  

class BNFQuestion(question.Question):

  NUM_EXAMPLE_SOLUTIONS = 6
  MAX_RULES_TO_GENERATE = 5
  MAX_RULE_LENGTH = 5
  MAX_SUBSTITUTIONS_PER_RULE = 3


  def __init__(
      self,
      rules : Dict[str,List[str]] = None,
      starting_rule : str = None
  ):

    if rules is None:
      # Then we should generate some rules
      num_rules_to_generate = random.randint(1, self.MAX_RULES_TO_GENERATE)

      rules = {
        c : [ ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase[:num_rules_to_generate], k=random.randint(1, self.MAX_RULE_LENGTH))) for _ in range(self.MAX_SUBSTITUTIONS_PER_RULE)]
        for c in string.ascii_uppercase[:num_rules_to_generate]
      }
      starting_rule = "A"


    self.rules = rules
    self.starting_rule = starting_rule

    example_solutions = set()
    log.info(f"Generating solutions")
    while len(example_solutions) < self.NUM_EXAMPLE_SOLUTIONS:
      # generate example str
      example_str : str = random.choice(self.rules[self.starting_rule])
      while any([r in example_str for r in self.rules.keys()]):
        log.info(f"example_str: \"{example_str}\"")
        for rule in self.rules.keys():
          for _ in range(example_str.count(rule)):
            example_str = example_str.replace(rule, random.choice(self.rules[rule]))
      example_solutions.add(example_str)
    log.info(f"example_solutions: {example_solutions}")


class BNFQuestion_rewriting(question.Question):
  # The goal is that this will be a simple example of one of the different kinds of rewriting we are doing.
  # The grammars will be super simple and mainly just use different forms of input
  # The kinds are:
  # 1. left recursion
  # 2. left factoring
  # 3. ugh, the one that doesn't seem like the right name
  
  # Questions will take the form of:
  # Given this rule, what auxiliary rule can we add?

  def get_question_prelude(self) -> List[str]:
    return [
      "Given the below information on a BNF, please correct the grammar.",
      "Note that the input grammar is defined as non-terminals which are upper-case letters within angle brackets (e.g. \"<A>\" is a non-terminal), "
      "while terminals are lowercase letters.",
    ]


class BNFQuestion_rewriting_left_recursion(BNFQuestion_rewriting):
  def __init__(self, alpha_length=5, beta_length=5):
    self.alpha = ''.join(random.choices(string.ascii_lowercase, k=alpha_length))
    self.beta = ''.join(random.choices(string.ascii_lowercase, k=beta_length))
    
    self.A = variable.Variable_BNFRule("<A>", [f"<A>{self.alpha}", f"{self.beta}"])
    self.A_prime = variable.Variable_BNFRule("<A'>", [f"{self.beta}<R>"])
    self.R = variable.Variable_BNFRule("<R>", [f"{self.alpha}<R>", "\"\""])
    
    super().__init__(
      given_vars=[
        self.A,
        self.A_prime
      ],
      target_vars=[
        self.R
      ]
    )
  
  def get_question_body(self) -> List[str]:
    question_lines = [
      "Given the input BNF grammar:\n"
      f"\t{self.A}\n",
      "What would replace `???` in the below grammar that has been corrected to fix left recursion?\n",
      f"\t{self.A_prime}\n",
      f"\t{self.R.name} : `???`\n"
    ]
    return question_lines

class BNFQuestion_rewriting_left_factoring(BNFQuestion_rewriting):
  def __init__(self, alpha_length=5, beta_length=5):
    self.alpha = ''.join(random.choices(string.ascii_lowercase, k=alpha_length))
    self.beta = ''.join(random.choices(string.ascii_lowercase, k=beta_length))
    
    # todo: make it so there are variables, and B and C are concrete rules (potentially)
    A_productions = sorted([
        f"{self.alpha}<B>",
        f"{self.alpha}<C>",
        f"{self.beta}<D>",
      ],
      key=(lambda _: random.random())
    )
    A_prime_productions = sorted([
      f"{self.alpha}<R>",
      f"{self.beta}<D>",
    ],
      key=(lambda _: random.random())
    )
    R_productions = ["<B>", "<C>"]
    
    self.A = variable.Variable_BNFRule("<A>", A_productions)
    self.A_prime = variable.Variable_BNFRule("<A'>", A_prime_productions)
    self.R = variable.Variable_BNFRule("<R>", R_productions)
    
    super().__init__(
      given_vars=[
        self.A,
        # self.R
      ],
      target_vars=[
        self.A_prime
      ]
    )
  
  def get_question_body(self) -> List[str]:
    question_lines = [
      "Given the input BNF grammar:\n"
      f"\t{self.A}\n",
      "What would replace `???` in the below grammar that has been updated by applying left factoring?\n",
      f"\t{self.A_prime.name} : `???`\n"
    ]
    return question_lines


class BNFQuestion_rewriting_nonterminal_expansion(BNFQuestion_rewriting):
  def __init__(self, alpha_length=5, beta_length=5, gamma_length=5):
    self.alpha = ''.join(random.choices(string.ascii_lowercase, k=alpha_length))
    self.beta = ''.join(random.choices(string.ascii_lowercase, k=beta_length))
    self.gamma = ''.join(random.choices(string.ascii_lowercase, k=beta_length))
    
    A_productions = sorted([
      f"{self.alpha}<B>",
      "<R>"
    ],
      key=(lambda _: random.random())
    )
    R_productions = sorted([
      f"{self.beta}<C>",
      f"{self.gamma}<D>",
    ],
      key=(lambda _: random.random())
    )
    
    A_prime_productions = [
      f"{self.alpha}<B>",
      f"{self.beta}<C>",
      f"{self.gamma}<D>",
    ]
    
    self.A = variable.Variable_BNFRule("<A>", A_productions)
    self.A_prime = variable.Variable_BNFRule("<A'>", A_prime_productions)
    self.R = variable.Variable_BNFRule("<R>", R_productions)
    
    super().__init__(
      given_vars=[
        self.A,
        self.R
      ],
      target_vars=[
        self.A_prime
      ]
    )
  
  def get_question_body(self) -> List[str]:
    question_lines = [
      "Given the input BNF grammar:\n"
      f"\t{self.A}\n",
      "What would replace `???` in the below grammar that has been updated by applying non-terminal expansion?\n",
      f"\t{self.A_prime.name} : `???`\n"
      f"\t{self.R}\n",
    ]
    return question_lines


class BNFQuestion_generation(question.Question):
  
  class BNF:
    def __init__(self, productions : Dict[str,List[str]], starting_nonterminal: str):
      self.productions = productions
      self.starting_nonterminal = starting_nonterminal
    
    def is_complete(self, str_to_test):
      return not any([nonterminal in str_to_test for nonterminal in self.productions.keys()])
    
    def get_string(self):
      curr_str = self.starting_nonterminal
      while (not self.is_complete(curr_str)):
        # do replacements
        pass
        for rule in self.productions.keys():
          for _ in range(curr_str.count(rule)):
            curr_str = curr_str.replace(rule, random.choice(self.productions[rule]))
      return curr_str
    
    def get_n_unique_strings(self, n: int):
      unique_strings = set()
      while (len(unique_strings) < n):
        unique_strings.add(self.get_string())
      return unique_strings
    
  
  # The goal of this will be to generate a number of examples and then mess them up somebody
  # the crux is how to mess them up in a way that is reasonably safe, which means wont produce a valid string
  
  # Questions will take the form of:
  # Given these rules, what are some valid strings?
  pass

def main():
  
  bnf = BNFQuestion_generation.BNF(
    productions={
      "<A>" : ["(<A>)", ""]
    },
    starting_nonterminal="<A>"
  )
  print(bnf.get_n_unique_strings(6))
  
  # q = BNFQuestion_rewriting_nonterminal_expansion()
  #
  # # print('\n'.join(q.get_question_prelude()))
  # # print('\n'.join(q.get_question_body()))
  #
  # print(
  #   BNFQuestion_rewriting_nonterminal_expansion().generate_group_markdown(1)
  # )
  
  
  #q.ask_question()
  
  
  
  # bnf_str = """
  # e1 ::= (e1) | ""
  # """
  #
  # bnf = BNF.create_bnf(bnf_str)
  
  # q = BNFQuestion(
  #   # rules = {
  #   #   "A" : ["aAa", ""]
  #   # },
  #   # starting_rule = "A"
  # )
  
  
  
  
if __name__ == "__main__":
  main()