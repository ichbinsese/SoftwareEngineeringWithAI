

"""
CMP--12 MotorHardwareInterface.

Traces:
- Component CMP--12
- Uses Waveshare.motor.Motor
"""

from __future__ import annotations
from typing import Tuple

from Waveshare.motor import Motor
from common.utils import clamp


class MotorHardwareInterface:
    """Low-level interface wrapping Waveshare Motor (motor_set)."""

    def __init__(self) -> None:
        self._motor = Motor()

    def apply_motor_command(self, left_speed: int, right_speed: int) -> None:
        """Apply clamped 0..100 speeds to hardware.

        Trace:
        - CMP--12 Execution
        """
        ls = int(clamp(left_speed, 0, 100))
        rs = int(clamp(right_speed, 0, 100))
        self._motor.set(ls, rs)

    def stop(self) -> None:
        self._motor.stop()

        