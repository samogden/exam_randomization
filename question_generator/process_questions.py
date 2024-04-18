#!env python
from __future__ import annotations

import abc
import enum
import random
from typing import List

from question import Question

from variable import Variable, VariableFloat

import dataclasses

import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

class SchedulingQuestion(Question, abc.ABC):
  class Kind(enum.Enum):
    FIFO = enum.auto()
    ShortestDuration = enum.auto()
    ShortestTimeRemaining = enum.auto()
    RoundRobin = enum.auto()
  
  MAX_JOBS = 5
  MAX_ARRIVAL_TIME = 20
  MAX_JOB_DURATION = 20
  
  ANSWER_EPSILON = 1.0
  
  SCHEDULER_NAME = None
  SELECTOR = None
  PREEMPTABLE = False
  TIME_QUANTUM = None
  
  ROUNDING_DIGITS = 2
  
  @dataclasses.dataclass
  class Job():
    arrival: float
    duration: float
    elapsed_time: float = 0
    response_time: float = None
    turnaround_time: float = None
    unpause_time: float | None = None
    last_run: float = 0
    
    SCHEDULER_EPSILON = 1e-09
    
    def run(self, curr_time) -> None:
      if self.response_time is None:
        # Then this is the first time running
        self.mark_start(curr_time)
      self.unpause_time = curr_time
      
    
    def stop(self, curr_time) -> None:
      self.elapsed_time += (curr_time - self.unpause_time)
      if self.is_complete(curr_time):
        self.mark_end(curr_time)
      self.unpause_time = None
      self.last_run = curr_time
    
    def mark_start(self, curr_time) -> None:
      logging.debug(f"starting {self.arrival} -> {self.duration} at {curr_time}")
      self.response_time = curr_time - self.arrival
    def mark_end(self, curr_time) -> None:
      logging.debug(f"ending {self.arrival} -> {self.duration} at {curr_time}")
      self.turnaround_time = curr_time - self.arrival
    
    def time_remaining(self, curr_time) -> float:
      time_remaining = self.duration
      time_remaining -= self.elapsed_time
      if self.unpause_time is not None:
        time_remaining -= (curr_time - self.unpause_time)
      return time_remaining
    
    def is_complete(self, curr_time) -> bool:
      # logging.debug(f"is complete: {self.duration} <= {self.elapsed_time} : {self.duration <= self.elapsed_time}")
      return self.duration <= self.elapsed_time + self.SCHEDULER_EPSILON # self.time_remaining(curr_time) <= 0
  
  def simulation(self, jobs_to_run: List[SchedulingQuestion.Job], selector, preemptable, time_quantum=None):
    curr_time = 0
    selected_job : SchedulingQuestion.Job | None = None
    while len(jobs_to_run) > 0:
      # logging.debug(f"curr_time: {curr_time :0.{self.ROUNDING_DIGITS}f}")
      # logging.debug("\n\n")
      # logging.debug(f"jobs_to_run: {jobs_to_run}")
      
      possible_time_slices = []
      
      # Get the jobs currently in the system
      available_jobs = list(filter(
        (lambda j: j.arrival <= curr_time),
        jobs_to_run
      ))
      
      # Get the jobs that will enter the system in the future
      future_jobs : List[SchedulingQuestion.Job] = list(filter(
        (lambda j: j.arrival > curr_time),
        jobs_to_run
      ))
      
      # logging.debug(f"available jobs: {available_jobs}")
      # logging.debug(f"future jobs: {future_jobs}")
      
      # Check whether there are jobs in the system already
      if len(available_jobs) > 0:
        # Use the selector to identify what job we are going to run
        selected_job : SchedulingQuestion.Job = min(
          available_jobs,
          key=(lambda j: selector(j, curr_time))
        )
        # We start the job that we selected
        selected_job.run(curr_time)
        
        # We could run to the end of the job
        possible_time_slices.append(selected_job.time_remaining(curr_time))
      
      # Check if we are preemptable or if we haven't found any time slices yet
      if preemptable or len(possible_time_slices) == 0:
        # Then when a job enters we could stop the current task
        if len(future_jobs) != 0:
          next_arrival : SchedulingQuestion.Job = min(
            future_jobs,
            key=(lambda j: j.arrival)
          )
          possible_time_slices.append( (next_arrival.arrival - curr_time))
      
      if time_quantum is not None:
        possible_time_slices.append(time_quantum)
      
      # logging.debug(f"possible_time_slices: {possible_time_slices}")
      
      ## Now we pick the minimum
      try:
        next_time_slice = min(possible_time_slices)
      except ValueError:
        logging.error("No jobs available to schedule")
        break
      curr_time += next_time_slice
      
      # We stop the job we selected, and potentially mark it as complete
      if selected_job is not None:
        selected_job.stop(curr_time)
      selected_job = None
      
      # Filter out completed jobs
      jobs_to_run : List[SchedulingQuestion.Job] = list(filter(
        (lambda j: not j.is_complete(curr_time)),
        jobs_to_run
      ))
      if len(jobs_to_run) == 0:
        break
    logging.debug(f"Completed in {curr_time}")
  
  
  def __init__(self, num_jobs=MAX_JOBS, max_arrival_time=MAX_ARRIVAL_TIME, max_duration=MAX_JOB_DURATION, single_target=True, **kwargs):
    if "kind" in kwargs:
      kind = kwargs["kind"]
    else:
      kind = random.choice(list(SchedulingQuestion.Kind))
    
    if kind == SchedulingQuestion.Kind.FIFO:
      # This is the default case
      self.SCHEDULER_NAME = "FIFO"
      self.SELECTOR = (lambda j, curr_time: j.arrival)
    elif kind == SchedulingQuestion.Kind.ShortestDuration:
      self.SCHEDULER_NAME = "Shortest Job First"
      self.SELECTOR = (lambda j, curr_time: j.duration)
    elif kind == SchedulingQuestion.Kind.ShortestTimeRemaining:
      self.SCHEDULER_NAME = "Shortest Remaining Time to Completion"
      self.SELECTOR = (lambda j, curr_time: j.time_remaining(curr_time))
      self.PREEMPTABLE = True
    elif kind == SchedulingQuestion.Kind.RoundRobin:
      self.SCHEDULER_NAME = "Round Robin"
      self.SELECTOR = (lambda j, curr_time: j.last_run)
      self.PREEMPTABLE = True
      self.TIME_QUANTUM = 1e-04
    else:
      # then we default to FIFO
      pass
    logging.debug(f"Running a {kind} simulation")
    
    # todo we could make this deterministic by either passing in a seed value or generating (and returning) one.  We'd have to re-run the simulation, but whatever
    if "jobs" in kwargs:
      logging.debug("Using given jobs")
      jobs = kwargs["jobs"]
    else:
      logging.debug("Generating new jobs")
      jobs = [
        SchedulingQuestion.Job(random.randint(0, max_arrival_time), random.randint(1, max_duration))
        for _ in range(num_jobs)
      ]
    
    logging.info("Starting simulation")
    self.simulation(jobs, self.SELECTOR, self.PREEMPTABLE, self.TIME_QUANTUM)
    logging.info("Ending simulation")
    
    self.job_stats = {
      i : {
        "arrival" : job.arrival,            # input
        "duration" : job.duration,          # input
        "response" : job.response_time,     # output
        "TAT" : job.turnaround_time         # output
      }
      for (i, job) in enumerate(jobs)
    }
    self.overall_stats = {
      "response" : sum([job.response_time for job in jobs]) / len(jobs),
      "TAT" : sum([job.turnaround_time for job in jobs]) / len(jobs)
    }
    
    given_variables = []
    target_variables = []
    for job_id in sorted(self.job_stats.keys()):
      given_variables.extend([
        Variable(f"Job{job_id} arrival", self.job_stats[job_id]["arrival"]),
        Variable(f"Job{job_id} duration", self.job_stats[job_id]["duration"])
      ])
    
    
    if single_target:
      # Then we pick one of the overalls, since this is a canvas quiz
      self.target = random.choice(["response", "TAT"])
      target_variables = [
        VariableFloat(f"Average {self.target.title()} Time", self.overall_stats[self.target]),
      ]
    else:
      for job_id in sorted(self.job_stats.keys()):
        target_variables.extend([
          VariableFloat(f"Job{job_id} Response Time", self.job_stats["response"], epsilon=self.ANSWER_EPSILON),
          VariableFloat(f"Job{job_id} Turn Around Time (TAT)", self.job_stats["TAT"], epsilon=self.ANSWER_EPSILON)
        ])
      target_variables.extend([
        VariableFloat(f"Average Response Time", sum([job.response_time for job in jobs]) / len(jobs)),
        VariableFloat("Average Turnaround Time", sum([job.turnaround_time for job in jobs]) / len(jobs))
      ])
      
    super().__init__(
      given_vars=given_variables,
      target_vars=target_variables
    )
  
  def get_question_prelude(self):
    return [f"Given the below information, compute the required values if using {self.SCHEDULER_NAME} scheduling."]

  def get_explanation(self) -> List[str]:
    # todo: It is _very_ possible to make a diagram of this...
    
    # todo: We should vary the phrasing depending on if it's response or TAT
    explanation_lines = [
      f"To calculate the overall {self.target} time we want to first start by calculating the {self.target} of all of our individual jobs."
    ]
    # Give the general formula
    if self.target == "response":
      calculation_base = "start"
    else:
      calculation_base = "completion"
    explanation_lines.extend([
      "We do this by subtracting arrival time from the start time, which is",
      f"Job_{self.target} = Job_{calculation_base} - Job_arrival\n",
    ])
    
    # Individual job explanation
    explanation_lines.extend([
      f"For each of our {len(self.job_stats.keys())} jobs, this calculation would be:"
    ])
    # todo: make this more flexible
    if self.target == "response":
      explanation_lines.extend([
        f"Job{job_id}_{self.target} = {self.job_stats[job_id]['arrival'] + self.job_stats[job_id]['response']:0.{self.ROUNDING_DIGITS}f} - {self.job_stats[job_id]['arrival']:0.{self.ROUNDING_DIGITS}f} = {self.job_stats[job_id]['response']:0.{self.ROUNDING_DIGITS}f}"
        for job_id in sorted(self.job_stats.keys())
      ])
    else:
      explanation_lines.extend([
        f"Job{job_id}_{self.target} = {self.job_stats[job_id]['arrival'] + self.job_stats[job_id]['TAT']:0.{self.ROUNDING_DIGITS}f} - {self.job_stats[job_id]['arrival']:0.{self.ROUNDING_DIGITS}f} = {self.job_stats[job_id]['TAT']:0.{self.ROUNDING_DIGITS}f}"
        for job_id in sorted(self.job_stats.keys())
      ])
    
    explanation_lines.extend(["\n"])
    summation_line = ' + '.join([
      f"{self.job_stats[job_id][self.target]:0.{self.ROUNDING_DIGITS}f}" for job_id in sorted(self.job_stats.keys())
    ])
    
    explanation_lines.extend([
      f"We then calculate the average of these to find the average {self.target} time",
      f"Avg({self.target}) = ({summation_line}) / ({len(self.job_stats.keys())}) = {self.target_vars[0].true_value}"
    ])
    
    return explanation_lines
    


def main():
  q = SchedulingQuestion(
    jobs = [
      SchedulingQuestion.Job(6.0, 5.0),
      SchedulingQuestion.Job(5.0, 9.0),
      SchedulingQuestion.Job(1.0, 6.0),
      SchedulingQuestion.Job(3.0, 2.0),
      SchedulingQuestion.Job(1.0, 7.0),
    ]
  )
  for var in q.target_vars:
    print(var)
  # print(q.target_vars)


  
  
  
  if __name__ == "__main__":
    main()