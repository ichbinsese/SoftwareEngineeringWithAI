
# MotorAbstractionLayer.
# Trace:
#   - CMP--8 MotorAbstractionLayer
#   - Uses CMP--12 to send low-level motor_set commands
#   - Approximate distances for cell moves and turns.

from core.timing import monotonic_ms, elapsed_ms


class MotorAbstractionLayer:
    def __init__(self, config_mgr, motor_hw, logger):
        self._cfg = config_mgr
        self._hw = motor_hw
        self._logger = logger
        env = self._cfg.get_env_config()
        self._cell_size_cm = env["cell_size_cm"]
        self._current_motion = None  # ("type", duration_ms, start_ms, speed)
        self._speed_limits = self._cfg.get_speed_limits()

    def _speed_cm_s_to_motor_value(self, speed_cm_s, mode="exploration"):
        limits = self._speed_limits
        max_cmd = limits["max_motor_speed_exploration"]
        if mode == "second_run":
            max_cmd = limits["max_motor_speed_second_run"]
        # Assume 200 cm/s at motor=100 (DAT--5 note)
        cmd = int((speed_cm_s / 200.0) * 100.0)
        if cmd > max_cmd:
            cmd = max_cmd
        if cmd < 0:
            cmd = 0
        return cmd

    def start_move_forward_one_cell(self, speed_cm_s, mode="exploration"):
        # DAT--8 Execution: estimate duration from distance and speed
        if speed_cm_s <= 0:
            return
        distance = self._cell_size_cm
        duration_s = distance / speed_cm_s
        duration_ms = int(duration_s * 1000)
        cmd = self._speed_cm_s_to_motor_value(speed_cm_s, mode=mode)
        self._hw.motor_set(cmd, cmd)
        self._current_motion = ("forward", duration_ms, monotonic_ms(), cmd)
        self._logger.log(
            "Forward one cell started (cmd=%d, dur=%dms)" % (cmd, duration_ms),
            component="CMP--8",
        )

    def start_turn_90(self, speed_deg_s, direction="left", mode="exploration"):
        if speed_deg_s <= 0:
            return
        angle = 90.0
        duration_s = angle / speed_deg_s
        duration_ms = int(duration_s * 1000)
        # For rotation, use some fraction of translational limit
        cmd = self._speed_cm_s_to_motor_value(50.0, mode=mode)
        if direction == "left":
            self._hw.motor_set(-cmd, cmd)
        else:
            self._hw.motor_set(cmd, -cmd)
        self._current_motion = ("turn", duration_ms, monotonic_ms(), cmd, direction)
        self._logger.log(
            "Turn 90 %s started (cmd=%d, dur=%dms)" % (direction, cmd, duration_ms),
            component="CMP--8",
        )

    def stop_now(self):
        self._hw.stop()
        self._current_motion = None

    # Called frequently by MotionController to check if motion is complete
    def update(self):
        if self._current_motion is None:
            return None
        motion = self._current_motion
        motion_type = motion[0]
        duration_ms = motion[1]
        start_ms = motion[2]
        if elapsed_ms(start_ms) >= duration_ms:
            self.stop_now()
            self._logger.log("Motion complete (%s)" % motion_type, component="CMP--8")
            # distance and rotation estimates
            if motion_type == "forward":
                return ("forward_done", self._cell_size_cm)
            elif motion_type == "turn":
                direction = motion[4]
                return ("turn_done", 90.0, direction)
        return None
