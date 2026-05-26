
# SensorHardwareWrappers.
# Trace:
#   - CMP--11 SensorHardwareWrappers
#   - Uses Waveshare.ultrasonic_sensor.UltrasonicSensor
#   - Uses Waveshare.infrared.Infrared

from Waveshare.ultrasonic_sensor import UltrasonicSensor
from Waveshare.infrared import Infrared


class SensorHardwareWrappers:
    def __init__(self):
        self._ultrasonic = UltrasonicSensor()
        self._infrared = Infrared()

    # CMP--11 Execution
    def get_front_ultrasonic_distance_cm(self):
        # Wrapper to hardware; units are centimeters (CMP--11 Invariants)
        try:
            return self._ultrasonic.distance()
        except Exception:
            return None

    def get_ir_left_status(self):
        try:
            return 1 if self._infrared.dsl() else 0
        except Exception:
            return 0

    def get_ir_right_status(self):
        try:
            return 1 if self._infrared.dsr() else 0
        except Exception:
            return 0
