

"""
CMP--5 MotionControllerAndWallAvoidance.

This is a simplified implementation capturing main responsibilities:
- Execute GridPath as sequence of turns + forward moves.
- Use SensorProcessingModule processed data for collision avoidance.
- Detect stalls via timeouts and preempted collisions.

Traces:
- Component CMP--5
- State machine FSM--2
- Data DAT--6 (collision-free motion)
"""

from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
import time

from common.types import (
    GridPath,
    DIR_NORTH,
    DIR_EAST,
    DIR_SOUTH,
    DIR_WEST,
    DIRECTION_VECTORS,
    rotate_left,
    rotate_right,
)
from common.utils import monotonic_time_s, log
from common.events import EventBus
from motion.motor_abstraction import MotorAbstractionLayer


class MotionControllerAndWallAvoidance:
    """Bridge between planner paths and motor abstraction, with collision checks."""

    def __init__(
        self,
        bus: EventBus,
        motion_cfg: Dict[str, Any],
        robot_geom_cfg: Dict[str, Any],
        cell_size_cm: float,
    ) -> None:
        """
        motion_cfg from ConfigurationManager.get_motion_safety_and_speed_config()
        robot_geom_cfg from ConfigurationManager.get_robot_geometry_config()
        """
        self._bus = bus
        self._cell_size_cm = cell_size_cm
        self.safety_margin_cm = float(motion_cfg["safety_margin_cm"])
        self.ultra_min = float(motion_cfg["ultrasonic_min_valid_cm"])
        self.ultra_max = float(motion_cfg["ultrasonic_max_valid_cm"])
        self.robot_radius_cm = float(robot_geom_cfg["robot_radius_cm"])
        self.uncertainty_margin_cm = float(robot_geom_cfg["uncertainty_margin_cm"])

        self.stall_timeout_per_cell_s = motion_cfg.get(
            "stall_timeout_per_cell_s", 3.0
        )
        self.max_obstacle_retries = motion_cfg.get("max_obstacle_retries", 3)

        self._mal = MotorAbstractionLayer(
            {
                "max_motor_speed_exploration": motion_cfg["max_motor_speed_exploration"],
                "max_motor_speed_second_run": motion_cfg[
                    "max_motor_speed_second_run"
                ],
            },
            robot_geom_cfg,
            cell_size_cm,
        )

        # Processed sensor feed (CMP--7 -> CMP--5)
        self.filtered_distance_cm: Optional[float] = None
        self.ir_left_obstacle = False
        self.ir_right_obstacle = False
        self._bus.subscribe("ProcessedSensorForMotion", self._on_processed_sensor)

        # Internal state (FSM--2)
        self._state = "MOTION_IDLE"
        self._current_heading = DIR_NORTH
        self._obstacle_retries = 0

    def _on_processed_sensor(self, data: Dict[str, Any]) -> None:
        self.filtered_distance_cm = data["filtered_ultrasonic_distance_cm"]
        self.ir_left_obstacle = data["ir_left_obstacle"]
        self.ir_right_obstacle = data["ir_right_obstacle"]

    # ---------- collision check (DAT--6) ----------

    def _can_continue_forward(self, speed_cm_s: float) -> bool:
        """Predict collision based on DAT--6 d_min."""
        if self.filtered_distance_cm is None:
            return True  # cannot judge; be permissive at low speeds

        stopping_distance = speed_cm_s * 0.2  # simple conservative model
        d_min = (
            self.robot_radius_cm
            + stopping_distance
            + self.safety_margin_cm
            + self.uncertainty_margin_cm
        )
        return self.filtered_distance_cm >= d_min

    # ---------- path execution ----------

    def execute_path(
        self,
        path: GridPath,
        start_heading: int,
        second_run: bool,
    ) -> Dict[str, Any]:
        """Execute a path; returns ExplorationMotionStatus / ReturnExecutionStatus / SecondRunExecutionStatus.

        Trace:
        - CMP--5 ExplorationPathExecuteRequest / ReturnPathExecuteRequest / SecondRunPathExecuteRequest.
        - FSM--2 transitions EXECUTING_MOVE / EXECUTING_TURN / PREEMPTED_FOR_COLLISION / STALL_PENDING.
        """
        self._current_heading = start_heading
        reached_target_cell = False
        cause_of_stop = "OK"
        executed_steps = 0

        if path.is_empty():
            return {
                "reached_target_cell": True,
                "cause_of_stop": "OK",
                "executed_steps": 0,
            }

        # For each move, perform heading alignment and forward cell transition.
        for move_dir in path.moves:
            # Determine required rotations to align current_heading with move_dir.
            while self._current_heading != move_dir:
                # Choose left or right (here simple; can be improved).
                # We rotate in place by 90Â° steps.
                self._state = "EXECUTING_TURN"
                deg, _ = self._mal.turn_left_90(second_run=second_run)
                self._current_heading = rotate_left(self._current_heading)

            # Now move forward one cell.
            self._state = "EXECUTING_MOVE"
            start_time = monotonic_time_s()
            # Determine approximate linear speed for collision computation.
            if second_run:
                motor_cmd = self._mal.max_motor_speed_second_run
            else:
                motor_cmd = self._mal.max_motor_speed_exploration
            speed_cm_s = (motor_cmd / 100.0) * self._mal.cm_per_second_at_100

            # Pre-motion collision check
            if not self._can_continue_forward(speed_cm_s):
                self._state = "PREEMPTED_FOR_COLLISION"
                self._mal.stop_now()
                self._obstacle_retries += 1
                if (
                    monotonic_time_s() - start_time >= self.stall_timeout_per_cell_s
                    or self._obstacle_retries >= self.max_obstacle_retries
                ):
                    self._state = "STALL_PENDING"
                    cause_of_stop = "STALL"
                    # Notify stall detection module (CMP--9)
                    self._bus.publish(
                        "StallDetected",
                        {
                            "current_heading": self._current_heading,
                            "elapsed_time": monotonic_time_s() - start_time,
                        },
                    )
                    return {
                        "reached_target_cell": False,
                        "cause_of_stop": cause_of_stop,
                        "executed_steps": executed_steps,
                    }
                else:
                    # try again next step; treat as preemption (DAT--6)
                    cause_of_stop = "COLLISION_PREVENTION"
                    return {
                        "reached_target_cell": False,
                        "cause_of_stop": cause_of_stop,
                        "executed_steps": executed_steps,
                    }

            # Move now
            dist, success = self._mal.move_forward_one_cell(second_run=second_run)
            self._state = "MOTION_IDLE"
            executed_steps += 1
            if not success:
                cause_of_stop = "MOTION_ERROR"
                break

        reached_target_cell = cause_of_stop == "OK"
        return {
            "reached_target_cell": reached_target_cell,
            "cause_of_stop": cause_of_stop,
            "executed_steps": executed_steps,
        }

        