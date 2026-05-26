
# MotionControllerAndWallAvoidance.
# Trace:
#   - CMP--5 MotionControllerAndWallAvoidance
#   - FSM--2 Motion controller FSM
#   - DAT--6 collision-free motion and braking distance
#
# This controller executes GridPath objects step by step using MotorAbstractionLayer,
# checking sensor data for collision avoidance and stall detection.

from core.enums import Direction
from core.timing import monotonic_ms, elapsed_ms


class MotionControllerState:
    MOTION_IDLE = 0
    EXECUTING_MOVE = 1
    EXECUTING_TURN = 2
    PREEMPTED_FOR_COLLISION = 3
    STALL_PENDING = 4


class MotionController:
    def __init__(self, config_mgr, sensor_proc, motor_abs, logger):
        self._cfg = config_mgr
        self._sensor = sensor_proc
        self._motor_abs = motor_abs
        self._logger = logger

        self._state = MotionControllerState.MOTION_IDLE
        self._current_path = None
        self._current_index = 0
        self._mode = "exploration"  # or "second_run" / "return"
        self._stall_handler = None

        stall_timeout_s, stall_max_retries = self._cfg.get_stall_config()
        self._stall_timeout_ms = int(stall_timeout_s * 1000)
        self._stall_max_retries = stall_max_retries
        self._stall_retry_count = 0
        self._motion_start_ms = 0

    def set_stall_handler(self, handler):
        self._stall_handler = handler

    # Request to execute a GridPath at exploration speeds
    # CMP--5: ExplorationPathExecuteRequest / ReturnPathExecuteRequest / SecondRunPathExecuteRequest
    def execute_path(self, grid_path, mode="exploration"):
        if grid_path is None or grid_path.is_empty():
            return
        self._current_path = grid_path
        self._current_index = 0
        self._mode = mode
        self._stall_retry_count = 0
        self._logger.log(
            "Executing path length %d, mode=%s" % (grid_path.length, mode),
            component="CMP--5",
        )
        self._schedule_next_segment()

    def _schedule_next_segment(self):
        if self._current_path is None:
            self._state = MotionControllerState.MOTION_IDLE
            return
        if self._current_index >= self._current_path.length:
            self._logger.log("Path execution complete.", component="CMP--5")
            self._state = MotionControllerState.MOTION_IDLE
            self._current_path = None
            return

        move_dir = self._current_path.moves[self._current_index]
        # For simplicity, each step: turn to desired direction then move one cell.
        # Here we assume robot already aligned; just move forward.
        # Real system would need heading management.

        # Check sensor precondition for forward move
        if not self._can_start_forward_motion():
            self._logger.warn(
                "Cannot start move due to obstacle in braking distance.",
                component="CMP--5",
            )
            # Treat as stall directly
            self._signal_stall("OBSTACLE_BEFORE_MOVE")
            return

        speeds = self._cfg.get_exploration_speeds()
        trans_speed = speeds[0]
        self._motor_abs.start_move_forward_one_cell(trans_speed, mode=self._mode)
        self._state = MotionControllerState.EXECUTING_MOVE
        self._motion_start_ms = monotonic_ms()
        self._logger.log(
            "Segment %d started (dir=%d)" % (self._current_index, move_dir),
            component="CMP--5",
        )

    # DAT--6 collision-free motion
    def _can_start_forward_motion(self):
        dist = self._sensor.get_filtered_ultrasonic_cm()
        if dist is None:
            # Be conservative: do not move if distance unknown
            return False
        safety = self._cfg.get_safety_config()
        env = self._cfg.get_env_config()
        speeds = self._cfg.get_exploration_speeds()
        trans_speed = speeds[0]
        stopping = self._cfg.stopping_distance_cm(trans_speed)
        d_min = (
            env["robot_radius_cm"]
            + stopping
            + safety["safety_margin_cm"]
            + env["uncertainty_margin_cm"]
        )
        return dist > d_min

    def _check_during_motion_collision(self):
        dist = self._sensor.get_filtered_ultrasonic_cm()
        if dist is None:
            return False
        safety = self._cfg.get_safety_config()
        env = self._cfg.get_env_config()
        speeds = self._cfg.get_exploration_speeds()
        trans_speed = speeds[0]
        stopping = self._cfg.stopping_distance_cm(trans_speed)
        d_min = (
            env["robot_radius_cm"]
            + stopping
            + safety["safety_margin_cm"]
            + env["uncertainty_margin_cm"]
        )
        if dist <= d_min:
            # Predictive collision - need stop
            self._logger.warn(
                "Predictive collision detected (dist=%.1f, d_min=%.1f)" % (dist, d_min),
                component="CMP--5",
            )
            return True
        return False

    def _signal_stall(self, reason):
        self._logger.warn(
            "Stall detected (%s)" % reason,
            component="CMP--5",
        )
        if self._stall_handler is not None:
            self._stall_handler.on_stall_detected(reason)

    # FSM--2 update
    def update(self):
        # Update MotorAbstraction layer (completion)
        result = self._motor_abs.update()
        if result is not None:
            if result[0] == "forward_done":
                if self._state == MotionControllerState.EXECUTING_MOVE:
                    self._current_index += 1
                    self._state = MotionControllerState.MOTION_IDLE
                    self._schedule_next_segment()
                return
            elif result[0] == "turn_done":
                # Not used in simplified path execution
                self._state = MotionControllerState.MOTION_IDLE
                return

        # During EXECUTING_MOVE, monitor for collision and stall
        if self._state == MotionControllerState.EXECUTING_MOVE:
            if self._check_during_motion_collision():
                # FSM--2: EXECUTING_MOVE -> PREEMPTED_FOR_COLLISION
                self._motor_abs.stop_now()
                self._state = MotionControllerState.PREEMPTED_FOR_COLLISION
                self._motion_start_ms = monotonic_ms()
                return
            if elapsed_ms(self._motion_start_ms) >= self._stall_timeout_ms:
                # Timeout for this cell move - treat as stall
                self._motor_abs.stop_now()
                self._signal_stall("TIMEOUT")
                self._state = MotionControllerState.STALL_PENDING
                return

        elif self._state == MotionControllerState.PREEMPTED_FOR_COLLISION:
            # If obstacle persists beyond timeout, convert to stall
            if elapsed_ms(self._motion_start_ms) >= self._stall_timeout_ms:
                self._signal_stall("COLLISION_PERSIST")
                self._state = MotionControllerState.STALL_PENDING

        elif self._state == MotionControllerState.STALL_PENDING:
            # Await external recovery; nothing to do here in this simple version
            pass

    # Called by StallDetectionAndRecovery after recovery plan executed
    def on_recovery_completed(self, success):
        if success:
            self._state = MotionControllerState.MOTION_IDLE
            self._stall_retry_count = 0
            self._logger.log("Recovery succeeded, resuming.", component="CMP--5")
            self._schedule_next_segment()
        else:
            self._logger.error("Recovery failed, motion halted.", component="CMP--5")
            self._state = MotionControllerState.MOTION_IDLE
            self._current_path = None
