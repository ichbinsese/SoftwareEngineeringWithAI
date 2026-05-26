
# Simple timing helpers.
# Trace:
#   - Used for mapping_time_budget_s (CMP--2, FSM--1)
#   - Used for stall timeouts (CMP--5, CMP--9, DAT--6)

import utime


def monotonic_ms():
    # Monotonic-ish milliseconds since boot (MicroPython).
    return utime.ticks_ms()


def elapsed_ms(start_ms):
    return utime.ticks_diff(monotonic_ms(), start_ms)
