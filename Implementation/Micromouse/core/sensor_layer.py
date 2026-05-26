

"""
Sensor Abstraction and Filtering Layer.

Traces:
- CMP--7 Sensor Abstraction and Filtering Layer
- DAT--5 Sensor Filtering and Consistency Parameters
"""

import time


class SensorAbstractionLayer:
    def __init__(self, ultrasonic, infrared, config):
        self.ultrasonic = ultrasonic
        self.infrared = infrared
        self.config = config

        self.ultra_buf = []
        self.ir_left_buf = []
        self.ir_right_buf = []

        self.has_valid_ultra = False
        self.has_valid_ir = False

        self.sensor_available = False

        self.last_filtered = {
            "ultra_cm": None,
            "ir_left": False,
            "ir_right": False,
            "timestamp_ms": 0,
        }

    # --- Public API used by Scheduler and others ---

    def sample_and_filter(self):
        """Perform one sampling and filtering step per control loop. (CMP--7.Execution)"""
        t_ms = time.ticks_ms()
        raw_ultra = self.ultrasonic.distance()
        # Validate ultrasonic
        if raw_ultra is not None and raw_ultra >= 0:
            self.has_valid_ultra = True
        else:
            # invalid, treat as no obstacle at large distance
            raw_ultra = 999.0

        raw_left = 1 if self.infrared.dsl() else 0
        raw_right = 1 if self.infrared.dsr() else 0
        # IR simple validity
        self.has_valid_ir = True

        self.ultra_buf.append(raw_ultra)
        self.ir_left_buf.append(raw_left)
        self.ir_right_buf.append(raw_right)

        if len(self.ultra_buf) > self.config.ultrasonic_window:
            self.ultra_buf.pop(0)
        if len(self.ir_left_buf) > self.config.ir_window:
            self.ir_left_buf.pop(0)
        if len(self.ir_right_buf) > self.config.ir_window:
            self.ir_right_buf.pop(0)

        # Moving average filter
        f_ultra = sum(self.ultra_buf) / len(self.ultra_buf)
        f_left = sum(self.ir_left_buf) / len(self.ir_left_buf)
        f_right = sum(self.ir_right_buf) / len(self.ir_right_buf)

        self.last_filtered = {
            "ultra_cm": f_ultra,
            "ir_left": f_left >= 0.5,
            "ir_right": f_right >= 0.5,
            "timestamp_ms": t_ms,
        }

        if self.has_valid_ultra and self.has_valid_ir:
            self.sensor_available = True

    def get_filtered(self):
        """Return last filtered sensor data (SAL_FilteredSensorData)."""
        return self.last_filtered

    def get_sensor_availability(self):
        """Return SensorAvailabilityStatus for CMP--1 (MissionControl)."""
        return self.sensor_available

        