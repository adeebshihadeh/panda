import time
import pytest
import random
import numpy as np
from unittest.mock import patch

from panda import Panda


def test_latency(p):
  N = 1000
  ts = []
  for _ in range(N):
    st = time.perf_counter_ns()
    p.get_type()
    et = time.perf_counter_ns()
    ts.append(et - st)
  ts = np.array(ts) / 1e6
  print(ts)
  print(sum(ts)/len(ts), max(ts), min(ts))


#def test_write_bandwidth(p):
#  pass

#def test_read_bandwidth(p):
#  pass

