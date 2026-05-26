

"""
CMP--1 ConfigurationManager implementation.

Responsibilities (CMP--1, DAT--5):
- Load configuration from file if present.
- Validate values against safety constraints, clamp or default as needed.
- Provide read-only accessors for other components.
"""

from __future__ import annotations
from typing import Dict, Any
import ujson as json  # MicroPython JSON module
import os

from common.utils import log, clamp


class ConfigurationManager:
    """
    Trace IDs:
    - Component: CMP--1
    - Data: DAT--5 (configuration parameters and validation)
    """

    CONFIG_PATH = "config.json"

    def __init__(self) -> None:
        self._config: Dict[str, Any] = {}
        self.flags = {
            "CONFIG_DEFAULT_USED": False,
            "CONFIG_PARAM_CLAMPED": False,
            "CONFIG_FATAL": False,
        }
        self._load_and_validate()

    # ---------- loading / validation (CMP--1, DAT--5) ----------

    def _load_and_validate(self) -> None:
        raw: Dict[str, Any] = {}
        if self.CONFIG_PATH in os.listdir():
            try:
                with open(self.CONFIG_PATH, "r") as f:
                    raw = json.load(f)
            except Exception as exc:
                log("CMP--1: Failed to parse config.json: %r" % exc)
                self.flags["CONFIG_DEFAULT_USED"] = True
        else:
            log("CMP--1: config.json missing, using defaults")
            self.flags["CONFIG_DEFAULT_USED"] = True

        self._config["timing"] = self._validate_timing(raw.get("timing", {}))
        self._config["speed"] = self._validate_speed(raw.get("speed", {}))
        self._config["sensor_filter"] = self._validate_sensor_filter(
            raw.get("sensor_filter", {})
        )
        self._config["safety"] = self._validate_safety(
            raw.get("safety", {}), self._config["speed"]
        )
        self._config["env"] = self._validate_env(raw.get("env", {}))

        # Fatal configuration errors: env geometry must be valid.
        env = self._config["env"]
        if env["cell_size_cm"] <= 0 or env["wall_thickness_cm"] <= 0:
            log("CMP--1: Fatal geometry config; preventing exploration")
            self.flags["CONFIG_FATAL"] = True

    def _validate_timing(self, timing: Dict[str, Any]) -> Dict[str, Any]:
        # Defaults (DAT--5 safety defaults)
        mapping_time_budget_s = float(timing.get("mapping_time_budget_s", 300.0))
        if not (0.0 < mapping_time_budget_s <= 300.0):
            self.flags["CONFIG_PARAM_CLAMPED"] = True
            mapping_time_budget_s = 300.0

        stall_timeout_per_cell_s = float(timing.get("stall_timeout_per_cell_s", 3.0))
        if stall_timeout_per_cell_s <= 0:
            self.flags["CONFIG_PARAM_CLAMPED"] = True
            stall_timeout_per_cell_s = 3.0

        stall_max_retries = int(timing.get("stall_max_retries", 3))
        if stall_max_retries < 0:
            self.flags["CONFIG_PARAM_CLAMPED"] = True
            stall_max_retries = 3

        return {
            "mapping_time_budget_s": mapping_time_budget_s,
            "stall_timeout_per_cell_s": stall_timeout_per_cell_s,
            "stall_max_retries": stall_max_retries,
        }

    def _validate_speed(self, speed: Dict[str, Any]) -> Dict[str, Any]:
        # Limit translational speeds to < 200 cm/s (CMP--1 invariant)
        def _v(name: str, default: float) -> float:
            v = float(speed.get(name, default))
            if v <= 0 or v > 200.0:
                self.flags["CONFIG_PARAM_CLAMPED"] = True
                v = default
            return v

        exploration_trans = _v("exploration_trans_speed_cm_s", 40.0)
        exploration_rot = _v("exploration_rot_speed_deg_s", 90.0)
        second_run_trans = _v("second_run_trans_speed_cm_s", 80.0)
        second_run_rot = _v("second_run_rot_speed_deg_s", 180.0)

        max_motor_speed_exploration = int(speed.get("max_motor_speed_exploration", 70))
        max_motor_speed_second_run = int(speed.get("max_motor_speed_second_run", 85))
        max_motor_speed_exploration = int(clamp(max_motor_speed_exploration, 0, 100))
        max_motor_speed_second_run = int(clamp(max_motor_speed_second_run, 0, 100))

        return {
            "exploration_trans_speed_cm_s": exploration_trans,
            "exploration_rot_speed_deg_s": exploration_rot,
            "second_run_trans_speed_cm_s": second_run_trans,
            "second_run_rot_speed_deg_s": second_run_rot,
            "max_motor_speed_exploration": max_motor_speed_exploration,
            "max_motor_speed_second_run": max_motor_speed_second_run,
        }

    def _validate_sensor_filter(self, sf: Dict[str, Any]) -> Dict[str, Any]:
        def _int_range(name: str, default: int) -> int:
            v = int(sf.get(name, default))
            if v < 1 or v > 10:
                self.flags["CONFIG_PARAM_CLAMPED"] = True
                v = default
            return v

        ultrasonic_filter_window = _int_range("ultrasonic_filter_window", 5)
        ir_confirm_count = _int_range("ir_confirm_count", 3)
        ir_clear_count = _int_range("ir_clear_count", 3)

        return {
            "ultrasonic_filter_window": ultrasonic_filter_window,
            "ir_confirm_count": ir_confirm_count,
            "ir_clear_count": ir_clear_count,
        }

    def _validate_safety(self, safety: Dict[str, Any], speed_cfg: Dict[str, Any]) -> Dict[str, Any]:
        # Simplified braking table: constant stopping distance per speed regime.
        safety_margin_cm = float(safety.get("safety_margin_cm", 2.0))
        if safety_margin_cm <= 0:
            self.flags["CONFIG_PARAM_CLAMPED"] = True
            safety_margin_cm = 2.0

        ultrasonic_min_valid_cm = float(safety.get("ultrasonic_min_valid_cm", 2.0))
        ultrasonic_max_valid_cm = float(safety.get("ultrasonic_max_valid_cm", 100.0))
        if ultrasonic_min_valid_cm <= 0 or ultrasonic_min_valid_cm >= ultrasonic_max_valid_cm:
            self.flags["CONFIG_PARAM_CLAMPED"] = True
            ultrasonic_min_valid_cm = 2.0
            ultrasonic_max_valid_cm = 100.0

        # Stopping distance model (DAT--5/6): ensure d_min <= cell_size/2, adjusted later once env known.
        # Here we only ensure basic sanity; detailed enforcement is done in motion_controller using env config.
        return {
            "safety_margin_cm": safety_margin_cm,
            "ultrasonic_min_valid_cm": ultrasonic_min_valid_cm,
            "ultrasonic_max_valid_cm": ultrasonic_max_valid_cm,
        }

    def _validate_env(self, env: Dict[str, Any]) -> Dict[str, Any]:
        cell_size_cm = float(env.get("cell_size_cm", 17.2))
        wall_thickness_cm = float(env.get("wall_thickness_cm", 1.6))
        if cell_size_cm <= 0 or wall_thickness_cm <= 0:
            self.flags["CONFIG_PARAM_CLAMPED"] = True
            cell_size_cm = 17.2
            wall_thickness_cm = 1.6
        return {
            "cell_size_cm": cell_size_cm,
            "wall_thickness_cm": wall_thickness_cm,
        }

    # ---------- accessors mapping to ConnectedComponents ----------

    # CMP--2 ExplorationTimingAndSpeedConfig
    def get_exploration_timing_and_speed(self) -> Dict[str, Any]:
        return {
            "mapping_time_budget_s": self._config["timing"]["mapping_time_budget_s"],
            "exploration_trans_speed_cm_s": self._config["speed"][
                "exploration_trans_speed_cm_s"
            ],
            "exploration_rot_speed_deg_s": self._config["speed"][
                "exploration_rot_speed_deg_s"
            ],
            "stall_timeout_per_cell_s": self._config["timing"][
                "stall_timeout_per_cell_s"
            ],
            "stall_max_retries": self._config["timing"]["stall_max_retries"],
        }

    # CMP--3 MapGeometryConfig
    def get_map_geometry_config(self) -> Dict[str, Any]:
        env = self._config["env"]
        return {
            "cell_size_cm": env["cell_size_cm"],
            "wall_thickness_cm": env["wall_thickness_cm"],
            "max_walls_per_cell": 3,
        }

    # CMP--4 PlannerConfig
    def get_planner_config(self) -> Dict[str, Any]:
        return {
            "use_diagonal_moves": False,
            "cost_per_step": 1,
        }

    # CMP--5 MotionSafetyAndSpeedConfig (DAT--6)
    def get_motion_safety_and_speed_config(self) -> Dict[str, Any]:
        speed = self._config["speed"]
        safety = self._config["safety"]
        env = self._config["env"]
        return {
            "exploration_trans_speed_cm_s": speed["exploration_trans_speed_cm_s"],
            "exploration_rot_speed_deg_s": speed["exploration_rot_speed_deg_s"],
            "second_run_trans_speed_cm_s": speed["second_run_trans_speed_cm_s"],
            "second_run_rot_speed_deg_s": speed["second_run_rot_speed_deg_s"],
            "max_motor_speed_exploration": speed["max_motor_speed_exploration"],
            "max_motor_speed_second_run": speed["max_motor_speed_second_run"],
            "safety_margin_cm": safety["safety_margin_cm"],
            "ultrasonic_min_valid_cm": safety["ultrasonic_min_valid_cm"],
            "ultrasonic_max_valid_cm": safety["ultrasonic_max_valid_cm"],
            "cell_size_cm": env["cell_size_cm"],
        }

    # CMP--6 SecondRunSpeedConfig
    def get_second_run_speed_config(self) -> Dict[str, Any]:
        speed = self._config["speed"]
        return {
            "second_run_trans_speed_cm_s": speed["second_run_trans_speed_cm_s"],
            "second_run_rot_speed_deg_s": speed["second_run_rot_speed_deg_s"],
            "max_second_run_speed_cm_s": speed["second_run_trans_speed_cm_s"],
        }

    # CMP--7 SensorFilterDebounceConfig
    def get_sensor_filter_debounce_config(self) -> Dict[str, Any]:
        sf = self._config["sensor_filter"]
        safety = self._config["safety"]
        return {
            "ultrasonic_filter_window_size": sf["ultrasonic_filter_window"],
            "ir_confirm_count": sf["ir_confirm_count"],
            "ir_clear_count": sf["ir_clear_count"],
            "min_valid_cm": safety["ultrasonic_min_valid_cm"],
            "max_valid_cm": safety["ultrasonic_max_valid_cm"],
        }

    # CMP--8 SpeedLimitConfig
    def get_speed_limit_config(self) -> Dict[str, Any]:
        speed = self._config["speed"]
        return {
            "max_motor_speed_exploration": speed["max_motor_speed_exploration"],
            "max_motor_speed_second_run": speed["max_motor_speed_second_run"],
        }

    # CMP--9 StallDetectionConfigParams
    def get_stall_detection_config(self) -> Dict[str, Any]:
        t = self._config["timing"]
        return {
            "move_timeout_per_cell_s": t["stall_timeout_per_cell_s"],
            "max_obstacle_retries": t["stall_max_retries"],
            "stall_replan_delay_s": 0.5,  # simple constant
        }

    # Robot geometry (CMP--9, CMP--8, DAT--6)
    def get_robot_geometry_config(self) -> Dict[str, Any]:
        return {
            "robot_radius_cm": 5.5,
            "uncertainty_margin_cm": 4.0,
        }

        