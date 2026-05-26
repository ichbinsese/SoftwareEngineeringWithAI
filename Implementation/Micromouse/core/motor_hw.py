
# MotorHardwareInterface.
# Trace:
#   - CMP--12 MotorHardwareInterface
#   - Uses Waveshare.motor.Motor

from Waveshare.motor import Motor


class MotorHardwareInterface:
    def __init__(self, logger):
        self._logger = logger
        self._motor = Motor()

    # CMP--12 Execution: apply speed commands
    def motor_set(self, left_speed, right_speed):
        # Clamp to 0..100 per CMP--12 Invariants
        if left_speed < 0:
            left_speed = 0
        if right_speed < 0:
            right_speed = 0
        if left_speed > 100:
            left_speed = 100
        if right_speed > 100:
            right_speed = 100
        self._motor.set(left_speed, right_speed)

    def stop(self):
        self._motor.stop()
