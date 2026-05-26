
# SensorProcessingModule.
# Trace:
#   - CMP--7 SensorProcessingModule
#   - FSM--4 sensor acquisition and filtering
#   - DAT--2 wall detection inputs
#   - DAT--6 collision-free motion (distance bounds)

from core.timing import monotonic_ms


class SensorProcessingModule:
    def __init__(self, config_mgr, sensor_hw, logger):
        self._cfg = config_mgr
        self._hw = sensor_hw
        self._logger = logger

        c = self._cfg.get_sensor_filter_config()
        self._window_size = c["ultrasonic_filter_window_size"]
        self._ir_confirm_count = c["ir_confirm_count"]
        self._ir_clear_count = c["ir_clear_count"]
        self._min_valid = c["min_valid_cm"]
        self._max_valid = c["max_valid_cm"]

        # Buffers for ultrasonic moving average
        self._us_values = []
        self._filtered_distance = None

        # IR debouncing state
        self._ir_left_confirmed = False
        self._ir_right_confirmed = False
        self._ir_left_counter = 0
        self._ir_right_counter = 0

        self._last_update_ms = monotonic_ms()

    # FSM--4 update loop: SENSOR_IDLE -> ACQUIRE_RAW -> FILTER_AND_DEBOUNCE -> UPDATE_OUTPUT
    def update(self):
        # ACQUIRE_RAW
        raw_us = self._hw.get_front_ultrasonic_distance_cm()
        raw_left = self._hw.get_ir_left_status()
        raw_right = self._hw.get_ir_right_status()

        # FILTER_AND_DEBOUNCE
        self._update_ultrasonic_filter(raw_us)
        self._update_ir_debounce(raw_left, raw_right)

        # UPDATE_OUTPUT - nothing to push actively; consumers call getters
        self._last_update_ms = monotonic_ms()

    # DAT--2 ultrasonic filter
    def _update_ultrasonic_filter(self, raw_us):
        if raw_us is None:
            return
        if raw_us < self._min_valid or raw_us > self._max_valid:
            # Out of physical bounds - CMP--7 Failures
            return

        self._us_values.append(raw_us)
        if len(self._us_values) > self._window_size:
            self._us_values.pop(0)
        self._filtered_distance = sum(self._us_values) / float(len(self._us_values))

    # DAT--2 IR debouncing
    def _update_ir_debounce(self, raw_left, raw_right):
        # Interpret non-zero as obstacle (LL-INTERF-3.2.1)
        left_obstacle = raw_left != 0
        right_obstacle = raw_right != 0

        # Left
        if left_obstacle:
            self._ir_left_counter += 1
            if self._ir_left_counter >= self._ir_confirm_count:
                self._ir_left_confirmed = True
                self._ir_left_counter = self._ir_confirm_count
        else:
            self._ir_left_counter -= 1
            if self._ir_left_counter <= -self._ir_clear_count:
                self._ir_left_confirmed = False
                self._ir_left_counter = -self._ir_clear_count

        # Right
        if right_obstacle:
            self._ir_right_counter += 1
            if self._ir_right_counter >= self._ir_confirm_count:
                self._ir_right_confirmed = True
                self._ir_right_counter = self._ir_confirm_count
        else:
            self._ir_right_counter -= 1
            if self._ir_right_counter <= -self._ir_clear_count:
                self._ir_right_confirmed = False
                self._ir_right_counter = -self._ir_clear_count

    # Public getters used by CMP--2, CMP--5
    def get_filtered_ultrasonic_cm(self):
        return self._filtered_distance

    def get_ir_left_obstacle(self):
        return self._ir_left_confirmed

    def get_ir_right_obstacle(self):
        return self._ir_right_confirmed

    # CMP--7: snapshot for SCAN_CELL
    def snapshot_for_cell_scan(self):
        return (
            self.get_filtered_ultrasonic_cm(),
            self.get_ir_left_obstacle(),
            self.get_ir_right_obstacle(),
        )
