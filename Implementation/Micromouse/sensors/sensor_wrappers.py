

"""
CMP--11 SensorHardwareWrappers.

Traces:
- Component CMP--11
- ConnectedComponents: provides raw ultrasonic and IR readings to CMP--7
"""

from __future__ import annotations
from typing import Optional

from Waveshare.ultrasonic_sensor import UltrasonicSensor  # hardware driver
from Waveshare.infrared import Infrared


class SensorHardwareWrappers:
    """Exclusive access to ultrasonic and infrared hardware."""

    def __init__(self) -> None:
        self._ultrasonic = UltrasonicSensor()
        self._ir = Infrared()

    # DAT--11 Execution comments:
    def get_front_ultrasonic_distance_cm(self) -> Optional[float]:
        """Return raw ultrasonic distance in cm (float).

        Trace:
        - CMP--11 Execution
        - DAT--2, DAT--6 use this as raw basis.
        """
        try:
            d = float(self._ultrasonic.distance())
            return d
        except Exception:
            # Mark invalid as None
            return None

    def get_ir_left_status(self) -> int:
        """Return raw left IR status (uint8_t-like).

        Non-zero => obstacle, zero => no obstacle (DAT--2, DAT--4).
        """
        try:
            return 1 if self._ir.dsl() else 0
        except Exception:
            return 0

    def get_ir_right_status(self) -> int:
        """Return raw right IR status (uint8_t-like)."""
        try:
            return 1 if self._ir.dsr() else 0
        except Exception:
            return 0

        