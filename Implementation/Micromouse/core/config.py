

"""
Configuration parameters.

Traces:
- DAT--2 Traversal Cost Model Parameters
- DAT--3 Time-Aware Planning and Nominal Cell Traversal Duration
- DAT--4 Ultrasonic Uncertainty and Clearance Checks
- DAT--5 Sensor Filtering and Consistency Parameters
- DAT--6 Motion Primitive Specification
"""

class Config:
    def __init__(self):
        # --- DAT--5: sampling frequency and filter windows ---
        self.sampling_frequency_hz = 20.0  # in [10,50], default 20
        self.control_loop_period_s = 1.0 / self.sampling_frequency_hz

        self.ultrasonic_window = 3
        self.ir_window = 3
        self.consistency_N = 3

        # --- DAT--3: time-aware planning parameters ---
        self.exploration_time_limit_ms = 5 * 60 * 1000  # 5 minutes
        # nominal traversal duration per cell (ms)
        self.nominal_cell_traversal_ms = 1000  # can be tuned

        # --- DAT--2: traversal cost profiles ---
        self.exploration_straight_cost = 1.0
        self.exploration_turn_penalty = 0.5

        # Second run: cost as time
        self.second_run_straight_cost = 1.0  # scaled appropriately
        self.second_run_turn_penalty = 0.5

        # --- DAT--4: ultrasonic and clearance model ---
        self.robot_radius_cm = 5.5
        self.wall_thickness_cm = 1.6
        self.cell_size_cm = 17.2
        self.clearance_margin_cm = 3.0
        self.ultrasonic_uncertainty_cm = 12.0

        # Emergency stop
        self.emergency_stop_distance_cm = 10.0  # conservative
        self.max_exploration_speed_cm_s = 10.0
        self.max_second_run_speed_cm_s = 15.0

        # --- DAT--6: motion primitives ---
        self.motion_primitive_cell_length_cm = self.cell_size_cm
        # motor speed range [0, 100]; map cm/s to percentage (simple linear scaling)
        self.motor_speed_scale = 5.0  # 1 speed unit ~= 5 cm/s

        # Rate limiting (CMP--8 invariant)
        self.max_speed_delta_per_cycle = 20  # motor units per cycle

        # Grid size (DAT--1)
        self.rows = 4
        self.cols = 8

        