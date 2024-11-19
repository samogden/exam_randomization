#!env python
from __future__ import annotations

import enum
import pprint
import re
from typing import List, Tuple, Dict, Type, Any

import pypandoc

from src.misc import OutputFormat
from src.question import Question, Answer

import random
import math
import collections

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class CachingQuestion(Question):
  
  class Kind(enum.Enum):
    FIFO = enum.auto()
    LRU = enum.auto()
    Belady = enum.auto()
    LFU = enum.auto()
    def __str__(self):
      return self.name
  
  
  class Cache:
    def __init__(self, kind : CachingQuestion.Kind, cache_size: int, all_requests : List[int]=None):
      self.kind = kind
      self.cache_size = cache_size
      self.all_requests = all_requests
      
      self.cache_state = [] # queue.Queue(maxsize=cache_size)
      self.last_used = collections.defaultdict(lambda: -math.inf)
      self.frequency = collections.defaultdict(lambda: 0)
    
    def query_cache(self, request, request_number):
      was_hit = request in self.cache_state
      
      evicted = None
      if was_hit:
        # hit!
        pass
      else:
        # miss!
        if len(self.cache_state) == self.cache_size:
          # Then we are full and need to evict
          evicted = self.cache_state[0]
          self.cache_state = self.cache_state[1:]
        
        # Add to cache
        self.cache_state.append(request)
      
      # update state variable
      self.last_used[request] = request_number
      self.frequency[request] += 1
      
      # update cache state
      if self.kind == CachingQuestion.Kind.FIFO:
        pass
      elif self.kind == CachingQuestion.Kind.LRU:
        self.cache_state = sorted(
          self.cache_state,
          key=(lambda e: self.last_used[e]),
          reverse=False
        )
      elif self.kind == CachingQuestion.Kind.LFU:
        self.cache_state = sorted(
          self.cache_state,
          key=(lambda e: (self.frequency[e], e)),
          reverse=False
        )
      elif self.kind == CachingQuestion.Kind.Belady:
        upcoming_requests = self.all_requests[request_number+1:]
        self.cache_state = sorted(
          self.cache_state,
          # key=(lambda e: (upcoming_requests.index(e), e) if e in upcoming_requests else (-math.inf, e)),
          key=(lambda e: (upcoming_requests.index(e), -e) if e in upcoming_requests else (math.inf, -e)),
          reverse=True
        )
      
      return (was_hit, evicted, self.cache_state)
  
  
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.num_elements = kwargs.get("num_elements", 5)
    self.cache_size = kwargs.get("cache_size", 3)
    self.num_requests = kwargs.get("num_requests", 10)
    
    self.instantiate()
  
  def instantiate(self):
    
    self.cache_policy = random.choice(list(self.Kind))
    
    self.requests = list(range(self.cache_size)) + random.choices(population=list(range(self.num_elements)), k=(self.num_requests))
    
    self.cache = CachingQuestion.Cache(self.cache_policy, self.cache_size, self.requests)
    
    self.request_results = {}
    number_of_hits = 0
    for (request_number, request) in enumerate(self.requests):
      was_hit, evicted, cache_state = self.cache.query_cache(request, request_number)
      if was_hit:
        number_of_hits += 1
      self.request_results[request_number] = {
        "request" : (f"[request]", request),
        "hit" : (f"[hit-{request_number}]", ('hit' if was_hit else 'miss')),
        "evicted" : (f"[evicted-{request_number}]", ('-' if evicted is None else f"{evicted}")),
        "cache_state" : (f"[cache_state-{request_number}]", ','.join(map(str, cache_state)))
      }
      self.answers.extend([
        Answer(f"hit-{request_number}",         ('hit' if was_hit else 'miss'),          Answer.AnswerKind.BLANK),
        Answer(f"evicted-{request_number}",     ('-' if evicted is None else f"{evicted}"),      Answer.AnswerKind.BLANK),
        Answer(f"cache_state-{request_number}", ','.join(map(str, cache_state)),  Answer.AnswerKind.BLANK),
      ])
      
      log.debug(f"{request:>2} | {'hit' if was_hit else 'miss':<4} | {evicted if evicted is not None else '':<3} | {str(cache_state):<10}")
      
    self.hit_rate = 100 * number_of_hits / (self.num_requests + 3)
    # self.hit_rate_var = VariableFloat("Hit Rate (%)", true_value=self.hit_rate)
    # self.blank_vars["hit_rate"] = self.hit_rate_var
    self.answers.extend([
      Answer("hit_rate", self.hit_rate, Answer.AnswerKind.BLANK)
    ])
  
  def get_body_lines(self, *args, **kwargs) -> List[str]:
    # return ["question"]
    lines = [
      f"Assume we are using a <b>{self.cache_policy}</b> caching policy and a cache size of <b>{self.cache_size}</b>."
      "",
      "Given the below series of requests please fill in the table.",
      "For the hit/miss column, please write either \"hit\" or \"miss\".",
      "For the eviction column, please write either the number of the evicted page or simply a dash (e.g. \"-\").",
      # "For the cache state, please enter the cache contents in the order suggested in class, separated by commas with no spaces (e.g. \"1,2,3\").",
      # "As a reminder, in class we kept them ordered in the order in which we would evict them from the cache (including Belady, although I was too lazy to do that in class)",
      "",
    ]
    
    table_headers = ["Page Requested", "Hit/Miss", "Evicted", "Cache State"]
    lines.extend(
      self.get_table_lines(
        { request_number :
          [
            request_number,
            f"[hit-{request_number}]",
            f"[evicted-{request_number}]",
            f"[cache_state-{request_number}]"
          ]
          for request_number in sorted(self.request_results.keys())
        },
        table_headers,
        sorted_keys=sorted(self.request_results.keys()),
        hide_keys=True
      )
    )
    
    lines.extend([
      "Hit rate, including compulsory misses and rounded to a single decimal place: [hit_rate]%"
    ])
    
    log.debug('\n'.join(lines))
    
    return lines
  
  def get_explanation_lines(self, *args, **kwargs) -> List[str]:
    log.debug("--------------------------------------------")
    log.debug("Get explanation lines")
    lines = [
      # "Apologies for the below table not including the eviction data, but technical limitations prevented me from including it.  "
      # "Instead, it can be inferred from the change in the cache state.",
      "The full table can be seen below.",
      ""
    ]
    
    log.debug(pprint.pformat(self.request_results))
    
    table_headers = ["Page", "Hit/Miss", "Evicted", "Cache State"]
    lines.extend(
      self.get_table_lines(
        { request_number :
          [
            self.request_results[request]["request"][1],
            self.request_results[request]["hit"][1],
            f'{self.request_results[request]["evicted"][1]}',
            f'{self.request_results[request]["cache_state"][1]}',
          ]
          for (request_number, request) in enumerate(sorted(self.request_results.keys()))
        },
        table_headers,
        sorted_keys=sorted(self.request_results.keys()),
        hide_keys=True
      )
    )
    
    lines.extend([
      "",
      "To calculate the hit rate we calculate the percentage of requests that were cache hits out of the total number of requests. "
      "In this case we are counting all requests, including compulsory misses."
    ])
    
    log.debug("******************* explanation *****************************")
    log.debug('\n'.join(lines))
    log.debug("******************* /explanation *****************************")
    
    return lines
    
