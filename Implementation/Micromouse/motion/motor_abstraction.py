

"""
CMP--8 MotorAbstractionLayer.

Traces:
- Component CMP--8
- Uses CMP--12 MotorHardwareInterface
- Uses ConfigurationManager SpeedLimitConfig and RobotGeometryAndBrakingConfig
"""

from __future__ import annotations
from typing import Dict, Any, Tuple
import time

from hardware.motor_interface import MotorHardwareInterface
from common.utils import clamp


class MotorAbstractionLayer:
    """Translate abstract move/turn commands into low-level speed commands."""

    def __init__(
        self,
        speed_cfg: Dict[str, Any],
        robot_geom_cfg: Dict[str, Any],
        cell_size_cm: float,
    ) -> None:
        """
        speed_cfg from ConfigurationManager.get_speed_limit_config()
        robot_geom_cfg from ConfigurationManager.get_robot_geometry_config()
        """
        self._hw = MotorHardwareInterface()
        self.max_motor_speed_exploration = int(
            speed_cfg["max_motor_speed_exploration"]
        )
        self.max_motor_speed_second_run = int(
            speed_cfg["max_motor_speed_second_run"]
        )
        self.robot_radius_cm = float(robot_geom_cfg["robot_radius_cm"])
        self.cell_size_cm = float(cell_size_cm)

        # Very simple mapping from speed to timing (no encoders).
        self.cm_per_second_at_100 = 100.0  # assumption for timing
        self.deg_per_second_at_100 = 180.0

    # ---------- mapping from motor command to velocity ----------

    def _time_for_distance(self, motor_speed: int, distance_cm: float) -> float:
        speed_cm_s = (motor_speed / 100.0) * self.cm_per_second_at_100
        if speed_cm_s <= 0:
            return 0
        return distance_cm / speed_cm_s

    def _time_for_rotation(self, motor_speed: int, degrees: float) -> float:
        speed_deg_s = (motor_speed / 100.0) * self.deg_per_second_at_100
        if speed_deg_s <= 0:
            return 0
        return degrees / speed_deg_s

    # ---------- abstract commands (CMP--8 AbstractMotionCommand) ----------

    def move_forward_one_cell(self, second_run: bool = False) -> Tuple[float, bool]:
        """Move roughly one cell center-to-center.

        Returns (distance_traveled_cm, success).
        """
        if second_run:
            cmd_speed = self.max_motor_speed_second_run
        else:
            cmd_speed = self.max_motor_speed_exploration

        t = self._time_for_distance(cmd_speed, self.cell_size_cm)
        self._hw.apply_motor_command(cmd_speed, cmd_speed)
        time.sleep(t)
        self._hw.stop()
        return (self.cell_size_cm, True)

    def move_forward_distance(
        self, distance_cm: float, second_run: bool = False
    ) -> Tuple[float, bool]:
        if second_run:
            cmd_speed = self.max_motor_speed_second_run
        else:
            cmd_speed = self.max_motor_speed_exploration

        distance_cm = float(distance_cm)
        t = self._time_for_distance(cmd_speed, distance_cm)
        self._hw.apply_motor_command(cmd_speed, cmd_speed)
        time.sleep(t)
        self._hw.stop()
        return (distance_cm, True)

    def turn_left_90(self, second_run: bool = False) -> Tuple[float, bool]:
        if second_run:
            cmd_speed = self.max_motor_speed_second_run
        else:
            cmd_speed = self.max_motor_speed_exploration

        t = self._time_for_rotation(cmd_speed, 90.0)
        self._hw.apply_motor_command(-cmd_speed, cmd_speed)
        time.sleep(t)
        self._hw.stop()
        return (90.0, True)

    def turn_right_90(self, second_run: bool = False) -> Tuple[float, bool]:
        if second_run:
            cmd_speed = self.max_motor_speed_second_run
        else:
            cmd_speed = self.max_motor_speed_exploration

        t = self._time_for_rotation(cmd_speed, 90.0)
        self._hw.apply_motor_command(cmd_speed, -cmd_speed)
        time.sleep(t)
        self._hw.stop()
        return (90.0, True)

    def stop_now(self) -> None:
        self._hw.stop()

        