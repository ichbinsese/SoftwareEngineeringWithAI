

"""
Mission Control State Machine.

Traces:
- CMP--1 Mission Control State Machine
- FSM--1 Mission State Machine
"""

from core.types import (
    MISSION_IDLE,
    MISSION_EXPLORE,
    MISSION_RETURN_TO_START,
    MISSION_SECOND_RUN,
    MISSION_COMPLETED,
)
from core.types import SECOND_RUN_NOT_EXECUTED, SECOND_RUN_SUCCESS, SECOND_RUN_FAILURE
from core.events import EventType


class MissionController:
    def __init__(
        self,
        grid_map,
        frontier,
        planner,
        goal_region,
        motion,
        exploration_status,
        sal,
        pose,
        event_queue,
        config,
    ):
        self.grid_map = grid_map
        self.frontier = frontier
        self.planner = planner
        self.goal_region = goal_region
        self.motion = motion
        self.exploration_status = exploration_status
        self.sal = sal
        self.pose = pose
        self.event_queue = event_queue
        self.config = config

        self.state = MISSION_IDLE
        self.mc_second_run_status = SECOND_RUN_NOT_EXECUTED
        self.init_completed = False

        self.mission_time_ms = 0

    # --- Inputs from Scheduler (CMP--10) ---

    def set_init_completed(self):
        """Called once initialization finishes. (CMP--10.Transmit InitCompletedFlag)"""
        self.init_completed = True

    def update_mission_time(self, t_ms):
        self.mission_time_ms = t_ms

    # --- Main control step, called once per control loop (CMP--1.Execution) ---

    def step(self):
        pose_est = self.pose.get_pose_estimate()
        sensor_avail = self.sal.get_sensor_availability()

        # Process queued events (DAT--7)
        events = self.event_queue.dequeue_all()
        exploration_completed = False
        exploration_timeout = False
        for ev in events:
            if ev.etype == EventType.EXPLORATION_COMPLETED:
                exploration_completed = True
            elif ev.etype == EventType.EXPLORATION_TIMEOUT:
                exploration_timeout = True

        # --- FSM--1 transitions and actions ---

        if self.state == MISSION_IDLE:
            # StateAction IDLE (FSM--1)
            if self.init_completed and sensor_avail:
                # Transition IDLE -> EXPLORE (FSM--1)
                self.exploration_status.on_explore_start(self.mission_time_ms)
                self.state = MISSION_EXPLORE

        elif self.state == MISSION_EXPLORE:
            # StateAction EXPLORE (FSM--1)
            elapsed_ms, remaining_ms = self.exploration_status.get_remaining_time_info()
            current_cell = pose_est["cell"]

            # Request frontier target and plan path
            target_info = self.frontier.select_target(current_cell, remaining_ms)
            if target_info is not None:
                # Use simple motor command that just drives forward at exploration speed
                speed = int(self.config.max_exploration_speed_cm_s / self.config.motor_speed_scale)
                cmd = {"left_speed": speed, "right_speed": speed}
                self.motion.set_motion_command(cmd)

            # Transition EXPLORE -> RETURN_TO_START (FSM--1)
            if exploration_completed or exploration_timeout:
                self.exploration_status.on_explore_stop()
                self.state = MISSION_RETURN_TO_START

        elif self.state == MISSION_RETURN_TO_START:
            # StateAction RETURN_TO_START (FSM--1)
            # For simplicity: when in this state, just stop motors and immediately
            # assume we are at start cell.
            self.motion.set_motion_command({"left_speed": 0, "right_speed": 0})
            # Transition RETURN_TO_START -> SECOND_RUN (FSM--1)
            # Start cell is (0,0) per DAT--1
            self.pose.cell = (0, 0)
            self.state = MISSION_SECOND_RUN
            self.mc_second_run_status = SECOND_RUN_NOT_EXECUTED

        elif self.state == MISSION_SECOND_RUN:
            # StateAction SECOND_RUN (FSM--1)
            # Select goal region and plan fastest path.
            start_cell = (0, 0)
            region = self.goal_region.select_region(start_cell)
            if region is None:
                # No region; treat as failure and end mission
                self.mc_second_run_status = SECOND_RUN_FAILURE
                self.state = MISSION_COMPLETED
            else:
                goal = region["target_cell"]
                path, cost = self.planner.plan_single(start_cell, goal, mode="SECOND_RUN")
                if path is None:
                    self.mc_second_run_status = SECOND_RUN_FAILURE
                    self.state = MISSION_COMPLETED
                else:
                    # Command higher speed run; simplified as straight drive
                    speed = int(self.config.max_second_run_speed_cm_s / self.config.motor_speed_scale)
                    cmd = {"left_speed": speed, "right_speed": speed}
                    self.motion.set_motion_command(cmd)
                    # For demo, immediately declare success
                    self.mc_second_run_status = SECOND_RUN_SUCCESS
                    self.state = MISSION_COMPLETED

        elif self.state == MISSION_COMPLETED:
            # StateAction COMPLETED (FSM--1)
            # No new motion commands
            self.motion.set_motion_command({"left_speed": 0, "right_speed": 0})

        