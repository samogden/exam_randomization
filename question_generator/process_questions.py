#!env python
from __future__ import annotations

import abc
import collections
import enum
import math
import os
import pprint
import random
import uuid
from typing import List, Tuple


import canvasapi
import canvasapi.course
import canvasapi.quiz

import matplotlib.colors

from .question import Question, CanvasQuestion
from .variable import Variable, VariableFloat

import dataclasses

import matplotlib.pyplot as plt

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

class SchedulingQuestion(Question, abc.ABC):
  class Kind(enum.Enum):
    FIFO = enum.auto()
    LIFO = enum.auto()
    ShortestDuration = enum.auto()
    ShortestTimeRemaining = enum.auto()
    RoundRobin = enum.auto()
  
  MAX_JOBS = 4
  MAX_ARRIVAL_TIME = 15
  MIN_JOB_DURATION = 2
  MAX_JOB_DURATION = 15
  
  ANSWER_EPSILON = 1.0
  
  SCHEDULER_KIND = None
  SCHEDULER_NAME = None
  SELECTOR = None
  PREEMPTABLE = False
  TIME_QUANTUM = None
  
  ROUNDING_DIGITS = 2
  
  @dataclasses.dataclass
  class Job():
    job_id: int
    arrival: float
    duration: float
    elapsed_time: float = 0
    response_time: float = None
    turnaround_time: float = None
    unpause_time: float | None = None
    last_run: float = 0               # When were we last scheduled
    
    state_change_times : List[float] = dataclasses.field(default_factory=lambda : [])
    
    SCHEDULER_EPSILON = 1e-09
    
    def run(self, curr_time, is_rr=False) -> None:
      if self.response_time is None:
        # Then this is the first time running
        self.mark_start(curr_time)
      self.unpause_time = curr_time
      if not is_rr:
        self.state_change_times.append(curr_time)
      
      
    def stop(self, curr_time, is_rr=False) -> None:
      self.elapsed_time += (curr_time - self.unpause_time)
      if self.is_complete(curr_time):
        self.mark_end(curr_time)
      self.unpause_time = None
      self.last_run = curr_time
      if not is_rr:
        self.state_change_times.append(curr_time)
    
    def mark_start(self, curr_time) -> None:
      log.debug(f"starting {self.arrival} -> {self.duration} at {curr_time}")
      self.start_time = curr_time
      self.response_time = curr_time - self.arrival + self.SCHEDULER_EPSILON
    def mark_end(self, curr_time) -> None:
      log.debug(f"ending {self.arrival} -> {self.duration} at {curr_time}")
      self.end_time = curr_time
      self.turnaround_time = curr_time - self.arrival + self.SCHEDULER_EPSILON
    
    def time_remaining(self, curr_time) -> float:
      time_remaining = self.duration
      time_remaining -= self.elapsed_time
      if self.unpause_time is not None:
        time_remaining -= (curr_time - self.unpause_time)
      return time_remaining
    
    def is_complete(self, curr_time) -> bool:
      # log.debug(f"is complete: {self.duration} <= {self.elapsed_time} : {self.duration <= self.elapsed_time}")
      return self.duration <= self.elapsed_time + self.SCHEDULER_EPSILON # self.time_remaining(curr_time) <= 0
    
    def has_started(self) -> bool:
      return self.response_time is None
  
  def simulation(self, jobs_to_run: List[SchedulingQuestion.Job], selector, preemptable, time_quantum=None):
    curr_time = 0
    selected_job : SchedulingQuestion.Job | None = None
    
    self.timeline = collections.defaultdict(list)
    self.timeline[curr_time].append("Simulation Start")
    for job in jobs_to_run:
      self.timeline[job.arrival].append(f"Job{job.job_id} arrived")
    
    while len(jobs_to_run) > 0:
      # log.debug(f"curr_time: {curr_time :0.{self.ROUNDING_DIGITS}f}")
      # log.debug("\n\n")
      # log.debug(f"jobs_to_run: {jobs_to_run}")
      
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
      
      # Check whether there are jobs in the system already
      if len(available_jobs) > 0:
        # Use the selector to identify what job we are going to run
        selected_job : SchedulingQuestion.Job = min(
          available_jobs,
          key=(lambda j: selector(j, curr_time))
        )
        if selected_job.has_started():
          self.timeline[curr_time].append(f"Starting Job{selected_job.job_id} (resp = {curr_time - selected_job.arrival:0.{self.ROUNDING_DIGITS}f}s)")
        # We start the job that we selected
        selected_job.run(curr_time, (self.SCHEDULER_KIND == self.Kind.RoundRobin))
        
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
      
      # log.debug(f"possible_time_slices: {possible_time_slices}")
      
      ## Now we pick the minimum
      try:
        next_time_slice = min(possible_time_slices)
      except ValueError:
        log.error("No jobs available to schedule")
        break
      if self.SCHEDULER_KIND != SchedulingQuestion.Kind.RoundRobin:
        if selected_job is not None:
          self.timeline[curr_time].append(f"Running Job{selected_job.job_id} for {next_time_slice:0.{self.ROUNDING_DIGITS}f}s")
        else:
          self.timeline[curr_time].append(f"(No job running)")
      curr_time += next_time_slice
      
      # We stop the job we selected, and potentially mark it as complete
      if selected_job is not None:
        selected_job.stop(curr_time, (self.SCHEDULER_KIND == self.Kind.RoundRobin))
        if selected_job.is_complete(curr_time):
          self.timeline[curr_time].append(f"Completed Job{selected_job.job_id} (TAT = {selected_job.turnaround_time:0.{self.ROUNDING_DIGITS}f}s)")
      selected_job = None
      
      # Filter out completed jobs
      jobs_to_run : List[SchedulingQuestion.Job] = list(filter(
        (lambda j: not j.is_complete(curr_time)),
        jobs_to_run
      ))
      if len(jobs_to_run) == 0:
        break
    log.debug(f"Completed in {curr_time}")
  
  
  def __init__(self,
      num_jobs=MAX_JOBS,
      max_arrival_time=MAX_ARRIVAL_TIME,
      min_duration=MIN_JOB_DURATION,
      max_duration=MAX_JOB_DURATION,
      single_target=True,
      **kwargs):
    if "kind" in kwargs:
      self.SCHEDULER_KIND = kwargs["kind"]
    else:
      self.SCHEDULER_KIND = random.choice(list(SchedulingQuestion.Kind))
    
    if self.SCHEDULER_KIND == SchedulingQuestion.Kind.FIFO:
      # This is the default case
      self.SCHEDULER_NAME = "FIFO"
      self.SELECTOR = (lambda j, curr_time: (j.arrival, j.job_id))
    elif self.SCHEDULER_KIND == SchedulingQuestion.Kind.ShortestDuration:
      self.SCHEDULER_NAME = "Shortest Job First"
      self.SELECTOR = (lambda j, curr_time: (j.duration, j.job_id))
    elif self.SCHEDULER_KIND == SchedulingQuestion.Kind.ShortestTimeRemaining:
      self.SCHEDULER_NAME = "Shortest Remaining Time to Completion"
      self.SELECTOR = (lambda j, curr_time: (j.time_remaining(curr_time), j.job_id))
      self.PREEMPTABLE = True
    elif self.SCHEDULER_KIND == SchedulingQuestion.Kind.LIFO:
      self.SCHEDULER_NAME = "LIFO"
      self.SELECTOR = (lambda j, curr_time: (-j.arrival, j.job_id))
      self.PREEMPTABLE = True
    elif self.SCHEDULER_KIND == SchedulingQuestion.Kind.RoundRobin:
      self.SCHEDULER_NAME = "Round Robin"
      self.SELECTOR = (lambda j, curr_time: (j.last_run, j.job_id))
      self.PREEMPTABLE = True
      self.TIME_QUANTUM = 1e-04
    else:
      # then we default to FIFO
      pass
    log.debug(f"Running a {self.SCHEDULER_KIND} simulation")
    
    # todo we could make this deterministic by either passing in a seed value or generating (and returning) one.  We'd have to re-run the simulation, but whatever
    if "jobs" in kwargs:
      log.debug("Using given jobs")
      jobs = kwargs["jobs"]
    else:
      log.debug("Generating new jobs")
      jobs = [
        SchedulingQuestion.Job(
          job_id,
          random.randint(0, max_arrival_time),
          random.randint(min_duration, max_duration)
        )
        for job_id in range(num_jobs)
      ]
    
    log.info("Starting simulation")
    self.simulation(jobs, self.SELECTOR, self.PREEMPTABLE, self.TIME_QUANTUM)
    log.info("Ending simulation")
    
    self.job_stats = {
      i : {
        "arrival" : job.arrival,            # input
        "duration" : job.duration,          # input
        "Response" : job.response_time,     # output
        "TAT" : job.turnaround_time,         # output
        "state_changes" : [job.arrival] + job.state_change_times + [job.arrival + job.turnaround_time],
      }
      for (i, job) in enumerate(jobs)
    }
    self.overall_stats = {
      "Response" : sum([job.response_time for job in jobs]) / len(jobs),
      "TAT" : sum([job.turnaround_time for job in jobs]) / len(jobs)
    }
    
    given_variables = []
    target_variables = []
    for job_id in sorted(self.job_stats.keys()):
      given_variables.extend([
        Variable(f"Job{job_id} arrival", self.job_stats[job_id]["arrival"]),
        Variable(f"Job{job_id} duration", self.job_stats[job_id]["duration"])
      ])
    
    # todo: make this less convoluted
    self.average_response_var = VariableFloat(f"Average Response Time", self.overall_stats["Response"] )
    self.average_tat_var = VariableFloat("Average Turnaround Time", self.overall_stats["TAT"])
    
    if single_target:
      # Then we pick one of the overalls, since this is a canvas quiz
      if self.SCHEDULER_KIND == SchedulingQuestion.Kind.RoundRobin:
        self.target = "TAT"
      else:
        self.target = random.choice(["Response", "TAT"])
      target_variables = [
        VariableFloat(f"Average {self.target} Time", self.overall_stats[self.target]),
      ]
    else:
      for job_id in sorted(self.job_stats.keys()):
        target_variables.extend([
          VariableFloat(f"Job{job_id} Response Time", self.job_stats["Response"], epsilon=self.ANSWER_EPSILON),
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
    return [f"Given the below information, compute the required values if using **{self.SCHEDULER_NAME}** scheduling.  Break any ties using the job number."]

  def get_question_body(self) -> List[str]:
    # todo: Make this give the values in a table so it is a bit more clear.  It also can let me bold it
    return self.get_table_lines(
      headers=["Arrival", "Duration"],
      table_data={
        f"Job{job_id}" : [self.job_stats[job_id]["arrival"], self.job_stats[job_id]["duration"]]
        for job_id in sorted(self.job_stats.keys())
      },
      add_header_space=True
    )
    
  
  def make_image(self, image_dir="imgs"):
    
    fig, ax = plt.subplots(1, 1)
    
    for x_loc in set([t for job_id in self.job_stats.keys() for t in self.job_stats[job_id]["state_changes"] ]):
      ax.axvline(x_loc, zorder=0)
      plt.text(x_loc + 0,len(self.job_stats.keys())-0.3,f'{x_loc:0.{self.ROUNDING_DIGITS}f}s',rotation=90)
    
    if self.SCHEDULER_KIND != self.Kind.RoundRobin:
      for y_loc, job_id in enumerate(sorted(self.job_stats.keys(), reverse=True)):
        for i, (start, stop) in enumerate(zip(self.job_stats[job_id]["state_changes"], self.job_stats[job_id]["state_changes"][1:])):
          ax.barh(
            y = [y_loc],
            left = [start],
            width = [stop - start],
            # color = 'white',
            edgecolor='black',
            linewidth = 2,
            color = 'white' if (i % 2 == 1) else 'black'
          )
    else:
      pass
      job_deltas = collections.defaultdict(int)
      for job_id in self.job_stats.keys():
        job_deltas[self.job_stats[job_id]["state_changes"][0]] += 1
        job_deltas[self.job_stats[job_id]["state_changes"][1]] -= 1
      log.debug(f"job_deltas: {job_deltas}")
    
      regimes_ranges = zip(sorted(job_deltas.keys()), sorted(job_deltas.keys())[1:])
      
      for (low, high) in regimes_ranges:
        log.debug(f"(low, high): {(low, high)}")
        jobs_in_range = [
          i for i, job_id in enumerate(list(self.job_stats.keys())[::-1])
          if
            (self.job_stats[job_id]["state_changes"][0] <= low)
            and
            (self.job_stats[job_id]["state_changes"][1] >= high)
        ]
        
        log.debug(f"jobs_in_range: {jobs_in_range}")
        if len(jobs_in_range) == 0: continue
        # continue
        ax.barh(
          y = jobs_in_range,
          left = [low for _ in jobs_in_range],
          width = [high - low for _ in jobs_in_range],
          color=f"{ 1 - ((len(jobs_in_range) - 1) / (len(self.job_stats.keys())))}",
          # edgecolor='blue',
          # linewidth=2,
        )
        # The core idea is that we want to track how many jobs are running in parallel and color the bars based on that
    
    
    # Plot the overall TAT
    ax.barh(
      y = [i for i in range(len(self.job_stats))][::-1],
      left = [self.job_stats[job_id]["arrival"] for job_id in sorted(self.job_stats.keys())],
      width = [self.job_stats[job_id]["TAT"] for job_id in sorted(self.job_stats.keys())],
      tick_label = [f"Job{job_id}" for job_id in sorted(self.job_stats.keys())],
      color=(0,0,0,0),
      edgecolor='black',
      linewidth=2,
      # hatch='/'
    )
    
    
    ax.set_xlim(xmin=0)
    # plt.show()
    
    if not os.path.exists(image_dir): os.mkdir(image_dir)
    image_path = os.path.join(image_dir, f"{uuid.uuid4()}.png")
    plt.savefig(image_path)
    
    self.img = image_path
    return image_path
  
  
  def get_explanation(
      self,
      *args,
      image_dir="imgs",
      **kwargs
  ) -> List[str]:
    log.debug("get_explanation")
    
    # todo: We should vary the phrasing depending on if it's response or TAT
    explanation_lines = []
    
    explanation_lines.extend([
      f"To calculate the overall {self.target} time we want to first start by calculating the {self.target} of all of our individual jobs."
    ])
    
    # Give the general formula
    if self.target == "Response":
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
    if self.target == "Response":
      explanation_lines.extend([
        f"Job{job_id}_{self.target} = {self.job_stats[job_id]['arrival'] + self.job_stats[job_id]['Response']:0.{self.ROUNDING_DIGITS}f} - {self.job_stats[job_id]['arrival']:0.{self.ROUNDING_DIGITS}f} = {self.job_stats[job_id]['Response']:0.{self.ROUNDING_DIGITS}f}"
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
      f"Avg({self.target}) = ({summation_line}) / ({len(self.job_stats.keys())}) = {self.target_vars[0].true_value:0.{self.ROUNDING_DIGITS}f}"
    ])
    
    explanation_lines.extend(
      self.get_table_lines(
        headers=["Time", "Events"],
        table_data={
          f"{t:02.{self.ROUNDING_DIGITS}f}s" : ['\n'.join(self.timeline[t])]
          for t in sorted(self.timeline.keys())
        },
        sorted_keys=[f"{t:02.{self.ROUNDING_DIGITS}f}s" for t in sorted(self.timeline.keys())],
      )
    )
    
    image_path = self.make_image(image_dir)
    
    explanation_lines.extend(
      [f"![Illustration of job execution.  White is running, grey is not running and red lines are job entry/exit points.]({image_path})"]
    )
    
    return explanation_lines
    
class SchedulingQuestion_canvas(SchedulingQuestion, CanvasQuestion):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    
    for job_id in self.job_stats.keys():
      self.blank_vars.update({
        f"job{job_id}_response" : VariableFloat(f"Job{job_id} Response Time", self.job_stats[job_id]["Response"]),
        f"job{job_id}_tat" : VariableFloat(f"Job{job_id} TAT", self.job_stats[job_id]["TAT"]),
      })
    self.blank_vars.update({
      "average_response" : self.average_response_var,
      "average_tat" : self.average_tat_var
    })
  
  
  def get_question_prelude(self):
    return [
      f"Given the below information, compute the required values if using <b>{self.SCHEDULER_NAME}</b> scheduling.  Break any ties using the job number.",
      "Please round all answers to 1 decimal place (even if they are whole numbers)."
    ]
  
  def get_question_body(self) -> List[str]:
    
    question_lines = self.get_question_prelude()
    
    question_lines.extend(
      self.get_table_lines(
        headers=["Arrival", "Duration", "Response Time", "TAT"],
        table_data={
          f"Job{job_id}" : [
            self.job_stats[job_id]["arrival"],
            self.job_stats[job_id]["duration"],
            f"[job{job_id}_response]",
            f"[job{job_id}_tat]",
          ]
          for job_id in sorted(self.job_stats.keys())
        },
        add_header_space=True
      )
    )
    
    question_lines.extend([
      f"Overall average response time: [average_response]",
      f"Overall average TAT: [average_tat]"
    ])
    
    
    return question_lines
  
  
  
  def get_explanation(
      self,
      course: canvasapi.course.Course,
      quiz: canvasapi.quiz.Quiz,
      image_dir="imgs",
  ) -> List[str]:
    log.debug("get_explanation")
    
    # todo: We should vary the phrasing depending on if it's response or TAT
    explanation_lines = []
    
    explanation_lines.extend([
      f"To calculate the overall Turnaround and Response times using {self.SCHEDULER_KIND} we want to first start by calculating the respective target and response times of all of our individual jobs."
    ])
    
    
    
    # Give the general formula
    explanation_lines.extend([
      "We do this by subtracting arrival time from either the completion time or the start time.  That is:"
      "",
      f"Job_TAT = Job_completion - Job_arrival\n",
      ""
      f"Job_response = Job_start - Job_arrival\n",
      "",
    ])
    
    # Individual job explanation
    explanation_lines.extend([
      f"For each of our {len(self.job_stats.keys())} jobs, we can make these calculations.",
      ""
    ])
    
    ## Add in TAT
    explanation_lines.extend([
      "For turnaround time (TAT) this would be:"
    ])
    explanation_lines.extend([
      f"Job{job_id}_{self.target} = {self.job_stats[job_id]['arrival'] + self.job_stats[job_id]['TAT']:0.{self.ROUNDING_DIGITS}f} - {self.job_stats[job_id]['arrival']:0.{self.ROUNDING_DIGITS}f} = {self.job_stats[job_id]['TAT']:0.{self.ROUNDING_DIGITS}f}"
      for job_id in sorted(self.job_stats.keys())
    ])
    explanation_lines.extend(["\n"])
    summation_line = ' + '.join([
      f"{self.job_stats[job_id][self.target]:0.{self.ROUNDING_DIGITS}f}" for job_id in sorted(self.job_stats.keys())
    ])
    explanation_lines.extend([
      f"We then calculate the average of these to find the average TAT time",
      f"Avg(TAT) = ({summation_line}) / ({len(self.job_stats.keys())}) = {self.overall_stats['TAT']:0.{self.ROUNDING_DIGITS}f}",
      "\n",
    ])
    
    
    ## Add in Response
    explanation_lines.extend([
      "For response time this would be:"
    ])
    explanation_lines.extend([
      f"Job{job_id}_{self.job_stats['Response']} = {self.job_stats[job_id]['arrival'] + self.job_stats[job_id]['Response']:0.{self.ROUNDING_DIGITS}f} - {self.job_stats[job_id]['arrival']:0.{self.ROUNDING_DIGITS}f} = {self.job_stats[job_id]['Response']:0.{self.ROUNDING_DIGITS}f}"
      for job_id in sorted(self.job_stats.keys())
    ])
    
    explanation_lines.extend(["\n"])
    summation_line = ' + '.join([
      f"{self.job_stats[job_id][self.target]:0.{self.ROUNDING_DIGITS}f}" for job_id in sorted(self.job_stats.keys())
    ])
    explanation_lines.extend([
      f"We then calculate the average of these to find the average Response time",
      f"Avg(Response) = ({summation_line}) / ({len(self.job_stats.keys())}) = {self.overall_stats['Response']:0.{self.ROUNDING_DIGITS}f}",
      "\n",
    ])
    
    explanation_lines.extend([
      "We can track these events either in a table or by drawing a diagram.  Note that in the diagram color corresponds to how many jobs are running at once, and events that happen at the same time may be merged together (i.e. there might not be 2N vertical lines for N jobs).",
      ""
    ])
    
    ## Add in table
    explanation_lines.extend(
      self.get_table_lines(
        headers=["Time", "Events"],
        table_data={
          f"{t:02.{self.ROUNDING_DIGITS}f}s" : ['\n'.join(self.timeline[t])]
          for t in sorted(self.timeline.keys())
        },
        sorted_keys=[f"{t:02.{self.ROUNDING_DIGITS}f}s" for t in sorted(self.timeline.keys())],
      )
    )
    
    # todo: see if I can move this out of this file, or somehow figure out the looping to make it not silly
    # it will probably be something along the lines of
    # 1. generate question
    # 2. Generate image from question information
    # 3. generate explanation with image generated
    image_path = self.make_image(image_dir)
    course.create_folder(f"{quiz.id}", parent_folder_path="Quiz Files")
    upload_success, f = course.upload(self.img, parent_folder_path=f"Quiz Files/{quiz.id}")
    
    log.debug(f"f: {f}")
    log.debug(f"f: {pprint.pformat(f)}")
    
    explanation_lines.extend(
      # [f"![Illustration of job execution.  White is running, grey is not running and red lines are job entry/exit points.]({image_path})"]
      [f"<img src=\"/courses/{course.id}/files/{f['id']}/preview\"\"/>"]
    )
    
    return explanation_lines

class ForkQuestion(CanvasQuestion):
  def __init__(self, *args, **kwargs):
    
    given_variables = []
    target_variables = []
    
    def generate_fork(chance_of_bad=0.5):
      if random.random() < chance_of_bad:
        return [
          f"int rc = fork({random.randint(0,127)})"
        ]
      else :
        return [
          f"int rc = fork()"
        ]
    def generate_check(change_of_bad=0.5):
      pass
    
    
    # Generate a C program that forks...
    
    # I think the idea is that it'll do random stuff.  Basically have a few blocks that will:
    # 1. fork off new processes
    # 2. check to see if it's the parent or child
    # 3. wait for processes
    # 4. exec something
    
    # Question can essentially be a multiple choice that they can say how it's doing, as either:
    # 1. yes this works as expected
    # 2. no, this does not appropriately catch child processes
    # 3. no, this does not appropriately exec
    # 4. no, this does not appropriately run
    # 5. no, other that's not listed
    
    # I can create this by having a series of functions that have a probability of generating a wrong answer that each time increases
    # (pass in a 0.25 and each time square it or something so it quickly will definitely produce an error)
    #
    
    super().__init__(
      given_vars=given_variables,
      target_vars=target_variables
    )


def main():
  q = ForkQuestion()
  for var in q.target_vars:
    print(var)
  # print(q.target_vars)
  
  print('\n'.join(q.get_question_body()))
  print('\n'.join(q.get_explanation()))
  
  
  
if __name__ == "__main__":
  main()