

"""
Motion Control and Collision Avoidance.

Traces:
- CMP--8 Motion Control and Collision Avoidance
- DAT--6 Motion Primitive Specification
"""

import time


class MotionController:
    MODE_NORMAL = 0
    MODE_AVOIDANCE = 1
    MODE_EMERGENCY_STOPPED = 2

    def __init__(self, motor, sal, config):
        self.motor = motor
        self.sal = sal
        self.config = config

        self.mode = self.MODE_NORMAL
        self.left_speed = 0
        self.right_speed = 0

        self.current_command = None  # dict from MissionControl

    def set_motion_command(self, cmd):
        """
        Receive MC_MotionCommand from MissionControl. (CMP--8.ConnectedComponents)
        cmd: dict with keys:
            - 'left_speed', 'right_speed' in [0,100]
        """
        self.current_command = cmd
        if self.mode == self.MODE_EMERGENCY_STOPPED:
            # Accept as new safe trajectory; resume NORMAL
            self.mode = self.MODE_NORMAL

    def _apply_rate_limit(self, target_left, target_right):
        dl = target_left - self.left_speed
        dr = target_right - self.right_speed
        max_delta = self.config.max_speed_delta_per_cycle
        if dl > max_delta:
            dl = max_delta
        if dl < -max_delta:
            dl = -max_delta
        if dr > max_delta:
            dr = max_delta
        if dr < -max_delta:
            dr = -max_delta
        self.left_speed += dl
        self.right_speed += dr

    def _emergency_check(self):
        """Check distance to obstacle and trigger emergency stop if needed. (CMP--8.Execution 2)"""
        data = self.sal.get_filtered()
        if not data:
            return
        d_cm = data["ultra_cm"]
        if d_cm is not None and d_cm <= self.config.emergency_stop_distance_cm:
            # Immediate stop
            self.motor.stop()
            self.left_speed = 0
            self.right_speed = 0
            self.mode = self.MODE_EMERGENCY_STOPPED

    def update(self):
        """
        Called once per control loop by Scheduler after mission planning. (CMP--8.Execution)
        """
        # Emergency stop if required (unless already stopped)
        if self.mode != self.MODE_EMERGENCY_STOPPED:
            self._emergency_check()

        if self.mode == self.MODE_EMERGENCY_STOPPED:
            # Ensure motors stopped
            self.motor.stop()
            self.left_speed = 0
            self.right_speed = 0
            return

        # Normal / avoidance (avoidance not implemented in detail here)
        target_left = 0
        target_right = 0
        if self.current_command:
            target_left = int(self.current_command.get("left_speed", 0))
            target_right = int(self.current_command.get("right_speed", 0))

        # Enforce maximum speed
        max_speed = 100
        if target_left > max_speed:
            target_left = max_speed
        if target_right > max_speed:
            target_right = max_speed

        # Apply rate limiting (CMP--8.Invariants)
        self._apply_rate_limit(target_left, target_right)

        # Send to hardware once per loop
        if self.left_speed == 0 and self.right_speed == 0:
            self.motor.stop()
        else:
            # Use set() (both wheels)
            self.motor.set(self.left_speed, self.right_speed)

        