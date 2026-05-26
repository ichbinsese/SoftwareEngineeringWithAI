

"""
CMP--7 SensorProcessingModule.

Traces:
- Component CMP--7
- State machine FSM--4
- Additional data DAT--2 (wall detection), DAT--6 (ranges)
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional

from common.utils import log
from common.events import EventBus
from .sensor_wrappers import SensorHardwareWrappers


class SensorProcessingModule:
    """Unified processing of ultrasonic + IR data."""

    def __init__(self, bus: EventBus, config: Dict[str, Any]) -> None:
        """
        config from ConfigurationManager.get_sensor_filter_debounce_config() (CMP--1->CMP--7).

        Keys:
        - ultrasonic_filter_window_size
        - ir_confirm_count
        - ir_clear_count
        - min_valid_cm
        - max_valid_cm
        """
        self._bus = bus
        self._hw = SensorHardwareWrappers()

        self.window_size = int(config["ultrasonic_filter_window_size"])
        self.ir_confirm_count = int(config["ir_confirm_count"])
        self.ir_clear_count = int(config["ir_clear_count"])
        self.min_valid_cm = float(config["min_valid_cm"])
        self.max_valid_cm = float(config["max_valid_cm"])

        self._us_window: List[float] = []
        self._left_count = 0
        self._right_count = 0
        self.left_obstacle_confirmed = False
        self.right_obstacle_confirmed = False
        self.filtered_distance_cm: Optional[float] = None

        # For SCAN_CELL snapshots (CMP--2<->CMP--7)
        self._scan_requested = False

    # ---------- Sampling and filtering loop (FSM--4) ----------

    def request_scan_snapshot(self) -> None:
        """Called by ExplorationStateMachineController (CMP--2 ScanRequest)."""
        self._scan_requested = True

    def step(self) -> None:
        """One acquisition/filter/update cycle.

        Maps to FSM--4 states:
        - SENSOR_IDLE -> ACQUIRE_RAW -> FILTER_AND_DEBOUNCE -> UPDATE_OUTPUT -> SENSOR_IDLE
        """
        # ACQUIRE_RAW
        d_raw = self._hw.get_front_ultrasonic_distance_cm()
        left_raw = self._hw.get_ir_left_status()
        right_raw = self._hw.get_ir_right_status()

        # FILTER_AND_DEBOUNCE (DAT--2)
        if d_raw is not None and self.min_valid_cm <= d_raw <= self.max_valid_cm:
            self._us_window.append(d_raw)
            if len(self._us_window) > self.window_size:
                self._us_window.pop(0)
            self.filtered_distance_cm = sum(self._us_window) / len(self._us_window)
        else:
            # invalid reading; ignore but keep previous filtered value
            pass

        # IR interpretation non-zero => obstacle (LL-INTERF-3.2.1)
        if left_raw != 0:
            self._left_count += 1
        else:
            self._left_count -= 1
        if right_raw != 0:
            self._right_count += 1
        else:
            self._right_count -= 1

        if self._left_count >= self.ir_confirm_count:
            self.left_obstacle_confirmed = True
            self._left_count = self.ir_confirm_count
        elif self._left_count <= -self.ir_clear_count:
            self.left_obstacle_confirmed = False
            self._left_count = -self.ir_clear_count

        if self._right_count >= self.ir_confirm_count:
            self.right_obstacle_confirmed = True
            self._right_count = self.ir_confirm_count
        elif self._right_count <= -self.ir_clear_count:
            self.right_obstacle_confirmed = False
            self._right_count = -self.ir_clear_count

        # UPDATE_OUTPUT
        processed = {
            "filtered_ultrasonic_distance_cm": self.filtered_distance_cm,
            "ir_left_obstacle": self.left_obstacle_confirmed,
            "ir_right_obstacle": self.right_obstacle_confirmed,
        }

        # Publish periodic data for motion controller (CMP--5 Receive ProcessedSensorDataForMotion)
        self._bus.publish("ProcessedSensorForMotion", processed)

        # If SCAN_CELL snapshot requested (CMP--2)
        if self._scan_requested:
            self._scan_requested = False
            self._bus.publish("CellScanSensorData", processed)

        