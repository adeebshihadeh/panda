#!/usr/bin/env python3
import unittest
import numpy as np
from panda import Panda
from panda.tests.safety import libpandasafety_py
from panda.tests.safety.common import PandaSafetyTest, make_msg, twos_comp


MAX_RATE_UP = 2
MAX_RATE_DOWN = 5
MAX_TORQUE = 150

MAX_RT_DELTA = 75
RT_INTERVAL = 250000

DRIVER_TORQUE_ALLOWANCE = 50;
DRIVER_TORQUE_FACTOR = 4;

IPAS_OVERRIDE_THRESHOLD = 200


class TestCadillacSafety(PandaSafetyTest, unittest.TestCase):

  TX_MSGS = [[0x151, 2], [0x152, 0], [0x153, 2], [0x154, 0]]

  @classmethod
  def setUp(cls):
    cls.safety = libpandasafety_py.libpandasafety
    cls.safety.set_safety_hooks(Panda.SAFETY_CADILLAC, 0)
    cls.safety.init_tests_cadillac()

  # override these inherited tests from PandaSafetyTest
  def test_relay_malfunction(self): pass
  def test_allow_brake_at_zero_speed(self): pass
  def test_not_allow_brake_when_moving(self): pass

  def _set_prev_torque(self, t):
    self.safety.set_cadillac_desired_torque_last(t)
    self.safety.set_cadillac_rt_torque_last(t)

  def _torque_driver_msg(self, torque):
    t = twos_comp(torque, 11)
    to_send = make_msg(0, 0x164)
    to_send[0].RDLR = ((t >> 8) & 0x7) | ((t & 0xFF) << 8)
    return to_send

  def _torque_msg(self, torque):
    to_send = make_msg(2, 0x151)
    t = twos_comp(torque, 14)
    to_send[0].RDLR = ((t >> 8) & 0x3F) | ((t & 0xFF) << 8)
    return to_send

  def test_default_controls_not_allowed(self):
    self.assertFalse(self.safety.get_controls_allowed())

  def test_enable_control_allowed_from_cruise(self):
    to_push = make_msg(0, 0x370)
    to_push[0].RDLR = 0x800000
    self._rx(to_push)
    self.assertTrue(self.safety.get_controls_allowed())

  def test_disable_control_allowed_from_cruise(self):
    to_push = make_msg(0, 0x370)
    self.safety.set_controls_allowed(1)
    self._rx(to_push)
    self.assertFalse(self.safety.get_controls_allowed())

  def test_torque_absolute_limits(self):
    for controls_allowed in [True, False]:
      for torque in np.arange(-MAX_TORQUE - 1000, MAX_TORQUE + 1000, MAX_RATE_UP):
        self.safety.set_controls_allowed(controls_allowed)
        self.safety.set_cadillac_rt_torque_last(torque)
        self.safety.set_cadillac_torque_driver(0, 0)
        self.safety.set_cadillac_desired_torque_last(torque - MAX_RATE_UP)

        if controls_allowed:
          send = (-MAX_TORQUE <= torque <= MAX_TORQUE)
        else:
          send = torque == 0

        self.assertEqual(send, self._tx(self._torque_msg(torque)))

  def test_non_realtime_limit_up(self):
    self.safety.set_cadillac_torque_driver(0, 0)
    self.safety.set_controls_allowed(True)

    self._set_prev_torque(0)
    self.assertTrue(self._tx(self._torque_msg(MAX_RATE_UP)))
    self._set_prev_torque(0)
    self.assertTrue(self._tx(self._torque_msg(-MAX_RATE_UP)))

    self._set_prev_torque(0)
    self.assertFalse(self._tx(self._torque_msg(MAX_RATE_UP + 1)))
    self.safety.set_controls_allowed(True)
    self._set_prev_torque(0)
    self.assertFalse(self._tx(self._torque_msg(-MAX_RATE_UP - 1)))

  def test_non_realtime_limit_down(self):
    self.safety.set_cadillac_torque_driver(0, 0)
    self.safety.set_controls_allowed(True)

  def test_exceed_torque_sensor(self):
    self.safety.set_controls_allowed(True)

    for sign in [-1, 1]:
      for t in np.arange(0, DRIVER_TORQUE_ALLOWANCE + 1, 1):
        t *= -sign
        self.safety.set_cadillac_torque_driver(t, t)
        self._set_prev_torque(MAX_TORQUE * sign)
        self.assertTrue(self._tx(self._torque_msg(MAX_TORQUE * sign)))

      self.safety.set_cadillac_torque_driver(DRIVER_TORQUE_ALLOWANCE + 1, DRIVER_TORQUE_ALLOWANCE + 1)
      self.assertFalse(self._tx(self._torque_msg(-MAX_TORQUE)))

    # spot check some individual cases
    for sign in [-1, 1]:
      driver_torque = (DRIVER_TORQUE_ALLOWANCE + 10) * sign
      torque_desired = (MAX_TORQUE - 10 * DRIVER_TORQUE_FACTOR) * sign
      delta = 1 * sign
      self._set_prev_torque(torque_desired)
      self.safety.set_cadillac_torque_driver(-driver_torque, -driver_torque)
      self.assertTrue(self._tx(self._torque_msg(torque_desired)))
      self._set_prev_torque(torque_desired + delta)
      self.safety.set_cadillac_torque_driver(-driver_torque, -driver_torque)
      self.assertFalse(self._tx(self._torque_msg(torque_desired + delta)))

      self._set_prev_torque(MAX_TORQUE * sign)
      self.safety.set_cadillac_torque_driver(-MAX_TORQUE * sign, -MAX_TORQUE * sign)
      self.assertTrue(self._tx(self._torque_msg((MAX_TORQUE - MAX_RATE_DOWN) * sign)))
      self._set_prev_torque(MAX_TORQUE * sign)
      self.safety.set_cadillac_torque_driver(-MAX_TORQUE * sign, -MAX_TORQUE * sign)
      self.assertTrue(self._tx(self._torque_msg(0)))
      self._set_prev_torque(MAX_TORQUE * sign)
      self.safety.set_cadillac_torque_driver(-MAX_TORQUE * sign, -MAX_TORQUE * sign)
      self.assertFalse(self._tx(self._torque_msg((MAX_TORQUE - MAX_RATE_DOWN + 1) * sign)))


  def test_realtime_limits(self):
    self.safety.set_controls_allowed(True)

    for sign in [-1, 1]:
      self.safety.init_tests_cadillac()
      self._set_prev_torque(0)
      self.safety.set_cadillac_torque_driver(0, 0)
      for t in np.arange(0, MAX_RT_DELTA, 1):
        t *= sign
        self.assertTrue(self._tx(self._torque_msg(t)))
      self.assertFalse(self._tx(self._torque_msg(sign * (MAX_RT_DELTA + 1))))

      self._set_prev_torque(0)
      for t in np.arange(0, MAX_RT_DELTA, 1):
        t *= sign
        self.assertTrue(self._tx(self._torque_msg(t)))

      # Increase timer to update rt_torque_last
      self.safety.set_timer(RT_INTERVAL + 1)
      self.assertTrue(self._tx(self._torque_msg(sign * (MAX_RT_DELTA - 1))))
      self.assertTrue(self._tx(self._torque_msg(sign * (MAX_RT_DELTA + 1))))


  def test_fwd_hook(self):
    # nothing allowed
    buss = list(range(0x0, 0x3))
    msgs = list(range(0x1, 0x800))

    for b in buss:
      for m in msgs:
        # assume len 8
        self.assertEqual(-1, self.safety.safety_fwd_hook(b, make_msg(b, m, 8)))


if __name__ == "__main__":
  unittest.main()
