#!/bin/env python

class Flow:

  def __init__(self, arrival, size):
    self.arrival = arrival
    self.original_size = size
    self.size = size
    self.ct = 0.0

  def update(self, capacity, max_dt):
    if self.size <= 0.0: return False  # Don't process if done

    if self.size/capacity > max_dt:  # Cannot finish in time interval given
      self.size -= capacity*max_dt
      self.ct += max_dt
      return False
    else:
      self.size = 0.0
      self.ct += self.size/capacity  # Add timeslice of completion
      return True

MAX_TIME = 300  # Max simulation time
RTT = 0.1
C = 2.4*1000000000/(1000*8) # Pkts/Sec
SHAPES = ['1.2', '2.2']

for shape in SHAPES:
  rcp_f = "../../rcp/pareto-flowSizes/logs/logFile-pareto-sh" + shape
  out_f = "logs/flowSizeVsDelay-sh" + shape

  flows = []
  active_flows = 0
  prev_ts = 0.0
  curr_ts = 0.0
  processed = 0

  f = open(rcp_f, 'r')
  # Go through each line and grab the flows and process in order
  for line in f:
    if line.startswith("stats"):
      # Found flow data in debug log
      datum = line.rsplit(' ')
      if datum[2] != 'start': continue # Ignore non-start stats

      # First point is arrival time in sec and second is the size
      curr_ts = float(datum[1])
      nextflow = Flow(curr_ts, float(datum[7]))

      # Time interval [prev_ts, curr_ts]
      if active_flows > 0:
        capacity = C/active_flows # Get fraction fair to number of active flows
        for flow in flows:
          # Go through flows and update for time interval
          if flow.update(capacity, curr_ts - prev_ts):
            active_flows -= 1

      active_flows += 1
      flows.append(nextflow)
      prev_ts = curr_ts
    if processed % 10000 == 0:
      print "Processed %d lines of log file." % (processed)
      if processed >= 100000:
        break
    processed += 1
  f.close()

  print "Completed reading file."

  # Finished processing files
  # There may be some flows still remaining
  if active_flows > 0:
    capacity = C/active_flows
    for flow in flows:
      # Let flows complete
      flow.update(capacity, MAX_TIME)

  print "Completed remaining flows."

  data = {}
  # Record data
  for flow in flows:
    try:
      # List value will be [count, sum, max]
      record = data[str(flow.original_size)]
      record[0] += 1
      record[1] += flow.ct
      record[2] = max(record[2], flow.ct)
    except KeyError:
      data[str(flow.original_size)] = [1, flow.ct, flow.ct]

  print "Completed calculations."

  out = open(out_f, 'w')
  for key, value in data:
    avgct = value[1] / value[0]
    maxct = value[2]

    out.write('%s 0 0 0 0 0 %.12f 0 %.12f\n' % (key, avgct, maxct))
  out.close()

  print "Done"



