import time
import pytest
import random
import numpy as np
from unittest.mock import patch

from panda import Panda

pytestmark = [
  pytest.mark.execution_timeout(45),
]


def timeit(f, n=1000):
  ts = []
  for _ in range(n):
    st = time.perf_counter_ns()
    f()
    et = time.perf_counter_ns()
    ts.append(et - st)
  ts = np.array(ts) / 1e6
  #print(ts)
  print()
  print(sum(ts)/len(ts), max(ts), min(ts))
  return ts

def test_latency(p):
  ts = timeit(p.get_type, n=20000)
  print("latency", np.mean(ts), "ms")


def test_write_bandwidth(p):
  # TODO: faster way?
  a = b"a"*5000
  def write():
    dat = p._handle.bulkWrite(11, a)
    assert dat == len(a)
  ts = timeit(write, n=20)
  kbps = (len(a) / np.mean(ts)) / 1e3
  print("write", kbps, "kbps")

def _test_read_bandwidth(p):
  def read():
    dat = p._handle.bulkRead(10, 220)
    print(len(dat))
  timeit(read, n=3)
