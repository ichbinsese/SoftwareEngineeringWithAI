

"""
Main entry point.

Wires together core components according to Design:
- CMP--1 ConfigurationManager
- CMP--3 MapManager
- CMP--4 GridPathPlanner
- CMP--7 SensorProcessingModule
- CMP--5 MotionControllerAndWallAvoidance
- CMP--9 StallDetectionAndRecovery
- CMP--6 RunController
- CMP--10 SecondRunResultEvaluatorAndReporter
- CMP--13 ExternalStatusLogger

State machines:
- FSM--1 ExplorationStateMachineController is largely stubbed (not fully implemented),
  but hooks for exploration start and termination events are present via RunController.
- FSM--2, FSM--4 behaviors are partially realized.

This main loop:
- Initializes all modules.
- Periodically steps SensorProcessingModule.
- For demonstration, triggers a synthetic ExplorationStartEvent and
  ExplorationTerminatedEvent so RunController+SecondRunResultEvaluator execute.
"""

from __future__ import annotations
import time

from common.events import EventBus
from common.utils import log
from config.configuration_manager import ConfigurationManager
from mapping.map_manager import MapManager
from planning.grid_path_planner import GridPathPlanner
from sensors.sensor_processing import SensorProcessingModule
from motion.motion_controller import MotionControllerAndWallAvoidance
from motion.stall_detection import StallDetectionAndRecovery
from run.run_controller import RunController
from run.second_run_evaluator import SecondRunResultEvaluatorAndReporter
from logging.external_status_logger import ExternalStatusLogger
from common.types import CellCoord


def main() -> None:
    # Global event bus
    bus = EventBus()

    # CMP--1
    cfg = ConfigurationManager()

    if cfg.flags["CONFIG_FATAL"]:
        log("Fatal configuration; aborting execution")
        return

    # CMP--3
    map_geom_cfg = cfg.get_map_geometry_config()
    map_manager = MapManager(map_geom_cfg)

    # CMP--4
    planner_cfg = cfg.get_planner_config()
    planner = GridPathPlanner(planner_cfg)

    # CMP--7
    sensor_cfg = cfg.get_sensor_filter_debounce_config()
    sensor_proc = SensorProcessingModule(bus, sensor_cfg)

    # CMP--5
    motion_cfg = cfg.get_motion_safety_and_speed_config()
    robot_geom_cfg = cfg.get_robot_geometry_config()
    motion = MotionControllerAndWallAvoidance(
        bus,
        motion_cfg,
        robot_geom_cfg,
        cell_size_cm=map_geom_cfg["cell_size_cm"],
    )

    # CMP--9
    stall_cfg = cfg.get_stall_detection_config()
    stall = StallDetectionAndRecovery(bus, stall_cfg)

    # CMP--6
    second_run_cfg = cfg.get_second_run_speed_config()
    run_ctrl = RunController(bus, planner, map_manager, motion, second_run_cfg)

    # CMP--10
    evaluator = SecondRunResultEvaluatorAndReporter(bus, map_manager)

    # CMP--13
    logger = ExternalStatusLogger(bus)

    log("System initialized; starting demo loop")

    # Demo: simulate exploration start and termination after short delay
    bus.publish("ExplorationStartEvent", {"reason": "MANUAL_TRIGGER"})
    start_time = time.ticks_ms()
    # Main loop: sample sensors at ~50 Hz, then after some time stop exploration.
    while True:
        sensor_proc.step()
        time.sleep(0.02)  # 50 Hz

        if time.ticks_diff(time.ticks_ms(), start_time) > 2000:
            # Simulate mapping completion event once
            bus.publish(
                "ExplorationTerminatedEvent",
                {"reason": "MAPPING_COMPLETE"},
            )
            # Allow second run handling to execute, then break.
            time.sleep(1.0)
            break

    log("Main demo completed")


if __name__ == "__main__":
    main()

        