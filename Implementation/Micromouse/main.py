
#!/usr/bin/env python3
# Main entry point for maze robot control on Raspberry Pi Pico (MicroPython).
# This file wires all components together following the design document.
#
# Traceability:
#   - CMP--1 ConfigurationManager
#   - CMP--2 ExplorationStateMachineController
#   - CMP--3 MapManager
#   - CMP--4 GridPathPlanner
#   - CMP--5 MotionControllerAndWallAvoidance
#   - CMP--6 RunController
#   - CMP--7 SensorProcessingModule
#   - CMP--8 MotorAbstractionLayer
#   - CMP--9 StallDetectionAndRecovery
#   - CMP--10 SecondRunResultEvaluatorAndReporter
#   - CMP--11 SensorHardwareWrappers
#   - CMP--12 MotorHardwareInterface
#   - CMP--13 ExternalStatusLogger
#
# State machines:
#   - FSM--1 Exploration FSM
#   - FSM--2 Motion controller FSM
#   - FSM--3 Run controller FSM
#   - FSM--4 Sensor processing FSM

import sys
import utime

from core.config_manager import ConfigurationManager  # CMP--1
from core.map_manager import MapManager               # CMP--3
from core.path_planner import GridPathPlanner         # CMP--4
from core.sensor_wrappers import SensorHardwareWrappers  # CMP--11
from core.sensor_processing import SensorProcessingModule  # CMP--7
from core.motor_hw import MotorHardwareInterface      # CMP--12
from core.motor_abstraction import MotorAbstractionLayer  # CMP--8
from core.motion_controller import MotionController   # CMP--5
from core.stall_recovery import StallDetectionAndRecovery  # CMP--9
from core.run_controller import RunController         # CMP--6
from core.exploration_controller import ExplorationController  # CMP--2
from core.result_evaluator import SecondRunResultEvaluatorAndReporter  # CMP--10
from core.logger import ExternalStatusLogger          # CMP--13
from core.enums import Direction
from core.timing import monotonic_ms


def main():
    # ----- Initialization sequence -----
    logger = ExternalStatusLogger()  # CMP--13

    # CMP--1: Configuration manager (DAT--5)
    config_mgr = ConfigurationManager(logger)

    # Load configuration from file if available
    config_mgr.load()

    # CMP--3: MapManager with grid map (DAT--1)
    map_manager = MapManager(config_mgr, logger)

    # CMP--4: Path planner using BFS (DAT--4)
    planner = GridPathPlanner(map_manager, config_mgr, logger)

    # CMP--11: Hardware wrappers for sensors
    sensor_hw = SensorHardwareWrappers()

    # CMP--7: Sensor processing module (FSM--4, DAT--2, DAT--6)
    sensor_proc = SensorProcessingModule(config_mgr, sensor_hw, logger)

    # CMP--12: Motor hardware interface
    motor_hw = MotorHardwareInterface(logger)

    # CMP--8: Motor abstraction layer
    motor_abs = MotorAbstractionLayer(config_mgr, motor_hw, logger)

    # CMP--5: Motion controller and wall avoidance (FSM--2)
    motion_ctrl = MotionController(config_mgr, sensor_proc, motor_abs, logger)

    # CMP--9: Stall detection and recovery
    stall_recovery = StallDetectionAndRecovery(config_mgr, map_manager, planner, motion_ctrl, logger)

    # Wire mutual references for stall communication (CMP--5 <-> CMP--9, CMP--2)
    motion_ctrl.set_stall_handler(stall_recovery)

    # CMP--10: Second run result evaluator
    result_eval = SecondRunResultEvaluatorAndReporter(map_manager, logger)

    # CMP--6: Run controller (FSM--3)
    run_ctrl = RunController(config_mgr, planner, motion_ctrl, map_manager, result_eval, logger)

    # CMP--2: Exploration controller (FSM--1)
    exploration = ExplorationController(
        config_mgr=config_mgr,
        map_manager=map_manager,
        planner=planner,
        sensor_proc=sensor_proc,
        motion_ctrl=motion_ctrl,
        stall_recovery=stall_recovery,
        run_controller=run_ctrl,
        logger=logger
    )

    # Finish wiring run/exploration events (CMP--2 <-> CMP--6, CMP--10)
    run_ctrl.set_exploration_controller(exploration)
    result_eval.set_run_controller(run_ctrl)

    # Initial pose: assume (0,0) and heading NORTH per platform (FSM--1 IDLE description)
    initial_heading = Direction.NORTH
    map_manager.initialize_start_and_goal_regions()
    map_manager.initialize_start_pose(initial_heading)

    logger.log("System initialized. Starting exploration...", component="MAIN")

    # Notify run controller that exploration will start
    run_ctrl.on_exploration_start_event()
    exploration.request_start()

    # ----- Main control loop -----
    # Coarse but sufficient cooperative scheduling. Each iteration should be fast (<20 ms).
    last_sensor_update = 0
    sensor_period_ms = 20  # 50 Hz per CMP--7 timing

    while True:
        now = monotonic_ms()

        # Periodic sensor acquisition + filtering (FSM--4)
        if now - last_sensor_update >= sensor_period_ms:
            sensor_proc.update()
            last_sensor_update = now

        # Motion controller FSM + supervision (FSM--2)
        motion_ctrl.update()

        # Exploration FSM (FSM--1)
        exploration.update()

        # Run controller FSM (FSM--3)
        run_ctrl.update()

        # Simple stop condition for demo: if run is complete, break
        if run_ctrl.is_run_complete():
            logger.log("Run complete, stopping main loop.", component="MAIN")
            break

        utime.sleep_ms(10)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Emergency stop on Ctrl+C in development.
        print("Stopped by user", file=sys.stderr)
        try:
            from Waveshare.motor import Motor
            m = Motor()
            m.stop()
        except Exception:
            pass
