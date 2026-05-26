

"""
Utility helpers.

Traces:
- CMP--1: logging of config issues
- CMP--13: log formatting
"""

from __future__ import annotations
import sys
import time
from typing import Any


def monotonic_time_s() -> float:
    """Return monotonic time in seconds.

    Used by:
    - CMP--2 ExplorationStateMachineController timing (mapping_time_budget)
    - CMP--5 MotionController stall timers
    - CMP--9 StallDetectionAndRecovery timeouts
    """
    # On MicroPython, time.ticks_ms() is monotonic; convert to seconds.
    return time.ticks_ms() / 1000.0


def log(msg: str) -> None:
    """Simple console logger (CMP--13 ExternalStatusLogger backing)."""
    ts = "%.3f" % monotonic_time_s()
    sys.stdout.write("[%s] %s\n" % (ts, msg))
    sys.stdout.flush()


def clamp(val: float, lo: float, hi: float) -> float:
    """Clamp val into [lo, hi]. Used by CMP--1, CMP--12."""
    if val < lo:
        return lo
    if val > hi:
        return hi
    return val

        