#!env python
from __future__ import annotations

import abc
import random
from typing import List

from question_generator import Question
from question_generator import Variable
from question_generator import VariableFloat

import dataclasses

import logging
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

class SchedulingQuestion(Question, abc.ABC):
  MAX_JOBS = 5
  MAX_ARRIVAL_TIME = 20
  MAX_JOB_DURATION = 20
  
  @abc.abstractmethod
  def get_scheduler_name(self):
    pass
  
  @dataclasses.dataclass
  class Job():
    arrival_time: float
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
      logging.debug(f"starting {self.arrival_time} -> {self.duration} at {curr_time}")
      self.response_time = curr_time - self.arrival_time
    def mark_end(self, curr_time) -> None:
      logging.debug(f"ending {self.arrival_time} -> {self.duration} at {curr_time}")
      self.turnaround_time = curr_time - self.arrival_time
    
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
      # logging.debug(f"curr_time: {curr_time :0.3f}")
      # logging.debug("\n\n")
      # logging.debug(f"jobs_to_run: {jobs_to_run}")
      
      possible_time_slices = []
      
      # Get the jobs currently in the system
      available_jobs = list(filter(
        (lambda j: j.arrival_time <= curr_time),
        jobs_to_run
      ))
      
      # Get the jobs that will enter the system in the future
      future_jobs : List[SchedulingQuestion.Job] = list(filter(
        (lambda j: j.arrival_time > curr_time),
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
            key=(lambda j: j.arrival_time)
          )
          possible_time_slices.append( ( next_arrival.arrival_time - curr_time) )
      
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
  
  def __init__(self, num_jobs=MAX_JOBS, max_arrival_time=MAX_ARRIVAL_TIME, max_duration=MAX_JOB_DURATION, selector=(lambda j, curr_time: j.arrival_time), preemptable=False, time_quantum=None, **kwargs):
    self.selector = selector
    self.preemptable = preemptable
    self.time_quantum = time_quantum
    
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
    self.simulation(jobs, self.selector, self.preemptable, self.time_quantum)
    logging.info("Ending simulation")
    
    given_variables = []
    target_variables = []
    for (i, job) in enumerate(jobs):
      logging.info(f"{job.response_time}, {job.turnaround_time}")
      given_variables.append(Variable(f"Job{i}_arrival, Job{i}_duration", (job.arrival_time, job.duration)))
      target_variables.extend([
        VariableFloat(f"Job{i}_RespT", job.response_time, 1.0),
        VariableFloat(f"Job{i}_TAT", job.turnaround_time, 1.0)
      ])
    target_variables.extend([
      VariableFloat("Average Response Time", sum([job.response_time for job in jobs]) / len(jobs)),
      VariableFloat("Average Turnaround Time", sum([job.turnaround_time for job in jobs]) / len(jobs))
    ])
    super().__init__(
      given_vars=given_variables,
      target_vars=target_variables
    )
  
  def get_question_prelude(self):
    return [f"Given the below information, compute the required values if using {self.get_scheduler_name()} scheduling."]

class SchedulerQuestion_FIFO(SchedulingQuestion):
  def get_scheduler_name(self):
    return "FIFO"

class SchedulerQuestion_ShortestDuration(SchedulingQuestion):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs, selector=(lambda j, curr_time: j.duration))
  def get_scheduler_name(self):
    return "Shortest Job First"

class SchedulerQuestion_ShortestTimeRemaining(SchedulingQuestion):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs, selector=(lambda j, curr_time: j.time_remaining(curr_time)), preemptable=True)
  def get_scheduler_name(self):
    return "Shortest Remaining Time to Completion"


class SchedulerQuestion_Roundrobin(SchedulingQuestion):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs, selector=(lambda j, curr_time: j.last_run), time_quantum=1e-04)
  
  def get_scheduler_name(self):
    return "Round Robin"


def main():
  q = SchedulerQuestion_Roundrobin(
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