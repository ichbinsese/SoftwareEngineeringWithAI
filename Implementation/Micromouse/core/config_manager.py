
# ConfigurationManager implementation.
# Trace:
#   - CMP--1 ConfigurationManager component
#   - Derived from DAT--5 (configuration parameters and validation)
#
# Provides:
#   - Safe defaults if file missing or invalid (CMP--1 Failures)
#   - Read-only accessors used by other components.

import ujson
import os


class ConfigurationManager:
    CONFIG_PATH = "config.json"  # simple JSON instead of INI for MicroPython

    def __init__(self, logger):
        self._logger = logger
        self._config = {}
        self._flags = {
            "CONFIG_DEFAULT_USED": False,
            "CONFIG_PARAM_CLAMPED": False,
        }
        # Defaults derived from DAT--5
        self._defaults = {
            "timing": {
                "mapping_time_budget_s": 300,
                "stall_timeout_per_cell_s": 3.0,
                "stall_max_retries": 3,
            },
            "speed": {
                "exploration_trans_speed_cm_s": 40,
                "exploration_rot_speed_deg_s": 90,
                "second_run_trans_speed_cm_s": 80,
                "second_run_rot_speed_deg_s": 180,
                "max_motor_speed_exploration": 70,
                "max_motor_speed_second_run": 85,
            },
            "sensor_filter": {
                "ultrasonic_filter_window": 5,
                "ir_confirm_count": 3,
                "ir_clear_count": 3,
            },
            "safety": {
                "braking_distance_table": None,  # simplified; see _stopping_distance_cm
                "safety_margin_cm": 2.0,
                "ultrasonic_min_valid_cm": 2.0,
                "ultrasonic_max_valid_cm": 100.0,
            },
            "env": {
                "cell_size_cm": 17.2,
                "wall_thickness_cm": 1.6,
                "robot_radius_cm": 5.5,
                "uncertainty_margin_cm": 4.0,
            },
        }

    # CMP--1 Execution: load and validate configuration
    def load(self):
        if not self._file_exists(self.CONFIG_PATH):
            self._logger.warn(
                "Configuration file missing. Using safe defaults.",
                component="CMP--1",
            )
            self._flags["CONFIG_DEFAULT_USED"] = True
            self._config = self._defaults.copy()
            return

        try:
            with open(self.CONFIG_PATH, "r") as f:
                raw = f.read()
            cfg = ujson.loads(raw)
        except Exception as exc:
            self._logger.warn(
                "Failed to parse config file (%s). Using defaults." % exc,
                component="CMP--1",
            )
            self._flags["CONFIG_DEFAULT_USED"] = True
            self._config = self._defaults.copy()
            return

        # Merge and validate sections
        self._config = {}
        for section in self._defaults:
            sec_defaults = self._defaults[section]
            raw_sec = cfg.get(section, {})
            validated = {}
            for key in sec_defaults:
                value = raw_sec.get(key, sec_defaults[key])
                validated[key] = self._validate_key(section, key, value, sec_defaults[key])
            self._config[section] = validated

        self._logger.log("Configuration loaded and validated.", component="CMP--1")

    def _file_exists(self, path):
        try:
            s = os.stat(path)
            return s[0] & 0x4000 == 0 or True
        except OSError:
            return False

    # DAT--5: validation rules
    def _validate_key(self, section, key, value, default):
        clamped = False
        if section == "timing" and key == "mapping_time_budget_s":
            if not isinstance(value, (int, float)) or value <= 0 or value > 300:
                value = 300
                clamped = True
        elif section == "timing" and key == "stall_timeout_per_cell_s":
            if not isinstance(value, (int, float)) or value <= 0:
                value = default
                clamped = True
        elif section == "timing" and key == "stall_max_retries":
            if not isinstance(value, int) or value < 0 or value > 10:
                value = default
                clamped = True
        elif section == "speed":
            if not isinstance(value, (int, float)) or value <= 0 or value > 200:
                value = default
                clamped = True
        elif section == "sensor_filter":
            if not isinstance(value, int) or value < 1 or value > 10:
                value = default
                clamped = True
        elif section == "safety":
            if key == "safety_margin_cm":
                if not isinstance(value, (int, float)) or value <= 0:
                    value = default
                    clamped = True
            elif key in ("ultrasonic_min_valid_cm", "ultrasonic_max_valid_cm"):
                if not isinstance(value, (int, float)) or value < 0:
                    value = default
                    clamped = True
        elif section == "env":
            if not isinstance(value, (int, float)) or value <= 0:
                value = default
                clamped = True

        if clamped:
            self._flags["CONFIG_PARAM_CLAMPED"] = True
            self._logger.warn(
                "Config parameter %s.%s clamped or defaulted." % (section, key),
                component="CMP--1",
            )
        return value

    # Accessors for other components (CMP--1 Transmit signals)
    # ExplorationTimingAndSpeedConfig - for CMP--2
    def get_mapping_time_budget_s(self):
        return self._config["timing"]["mapping_time_budget_s"]

    def get_exploration_speeds(self):
        return (
            self._config["speed"]["exploration_trans_speed_cm_s"],
            self._config["speed"]["exploration_rot_speed_deg_s"],
        )

    def get_second_run_speeds(self):
        return (
            self._config["speed"]["second_run_trans_speed_cm_s"],
            self._config["speed"]["second_run_rot_speed_deg_s"],
        )

    def get_stall_config(self):
        return (
            self._config["timing"]["stall_timeout_per_cell_s"],
            self._config["timing"]["stall_max_retries"],
        )

    def get_sensor_filter_config(self):
        sf = self._config["sensor_filter"]
        safety = self._config["safety"]
        return {
            "ultrasonic_filter_window_size": sf["ultrasonic_filter_window"],
            "ir_confirm_count": sf["ir_confirm_count"],
            "ir_clear_count": sf["ir_clear_count"],
            "min_valid_cm": safety["ultrasonic_min_valid_cm"],
            "max_valid_cm": safety["ultrasonic_max_valid_cm"],
        }

    def get_env_config(self):
        env = self._config["env"]
        return {
            "cell_size_cm": env["cell_size_cm"],
            "wall_thickness_cm": env["wall_thickness_cm"],
            "robot_radius_cm": env["robot_radius_cm"],
            "uncertainty_margin_cm": env["uncertainty_margin_cm"],
        }

    def get_safety_config(self):
        safety = self._config["safety"]
        env = self._config["env"]
        return {
            "safety_margin_cm": safety["safety_margin_cm"],
            "ultrasonic_min_valid_cm": safety["ultrasonic_min_valid_cm"],
            "ultrasonic_max_valid_cm": safety["ultrasonic_max_valid_cm"],
            "robot_radius_cm": env["robot_radius_cm"],
            "uncertainty_margin_cm": env["uncertainty_margin_cm"],
        }

    def get_speed_limits(self):
        sp = self._config["speed"]
        return {
            "max_motor_speed_exploration": sp["max_motor_speed_exploration"],
            "max_motor_speed_second_run": sp["max_motor_speed_second_run"],
        }

    def get_flags(self):
        return self._flags

    # Simple braking distance approximation (DAT--6 note: simplified)
    def stopping_distance_cm(self, speed_cm_s):
        # In real implementation, use braking_distance_table (DAT--6).
        # Here approximate with linear scaling: distance = k * speed
        k = 0.05  # 0.05 s stopping at full effort
        return speed_cm_s * k
