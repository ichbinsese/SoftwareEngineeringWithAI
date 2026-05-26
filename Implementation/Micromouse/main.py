

"""
Main entry point.

High-level wiring of components per CMP--10 (Scheduler and Initialization).
"""

from core.scheduler import Scheduler  # CMP--10
from core.sensor_layer import SensorAbstractionLayer  # CMP--7
from core.gridmap import GridMap  # CMP--3
from core.mapping import MappingModule  # CMP--6
from core.pose import PoseEstimator  # CMP--9
from core.frontier import FrontierGenerator  # CMP--2
from core.planner import PathPlanner  # CMP--4
from core.goal_region import GoalRegionSelector  # CMP--5
from core.motion_control import MotionController  # CMP--8
from core.mission_control import MissionController  # CMP--1
from core.exploration_status import ExplorationStatus  # CMP--11
from core.events import EventQueue  # DAT--7
from core.config import Config
from Waveshare.battery import Battery
from Waveshare.motor import Motor
from Waveshare.ultrasonic_sensor import UltrasonicSensor
from Waveshare.infrared import Infrared


def create_system():
    """Initialize all modules and wire dependencies. Traces: CMP--10, CMP--1..CMP--11."""
    config = Config()

    # Hardware objects
    battery = Battery()
    motor_hw = Motor()
    ultrasonic = UltrasonicSensor()
    infrared = Infrared()

    # Shared infra
    event_queue = EventQueue(size=16)  # DAT--7
    grid_map = GridMap(config=config)  # CMP--3
    pose = PoseEstimator(config=config)  # CMP--9
    sal = SensorAbstractionLayer(
        ultrasonic=ultrasonic,
        infrared=infrared,
        config=config,
    )  # CMP--7
    mapping = MappingModule(
        grid_map=grid_map,
        config=config,
    )  # CMP--6
    planner = PathPlanner(
        grid_map=grid_map,
        config=config,
    )  # CMP--4
    frontier = FrontierGenerator(
        grid_map=grid_map,
        planner=planner,
        config=config,
    )  # CMP--2
    goal_region = GoalRegionSelector(
        grid_map=grid_map,
        planner=planner,
        config=config,
    )  # CMP--5
    motion = MotionController(
        motor=motor_hw,
        sal=sal,
        config=config,
    )  # CMP--8
    exploration_status = ExplorationStatus(
        grid_map=grid_map,
        config=config,
        event_queue=event_queue,
    )  # CMP--11
    mission = MissionController(
        grid_map=grid_map,
        frontier=frontier,
        planner=planner,
        goal_region=goal_region,
        motion=motion,
        exploration_status=exploration_status,
        sal=sal,
        pose=pose,
        event_queue=event_queue,
        config=config,
    )  # CMP--1

    scheduler = Scheduler(
        config=config,
        sal=sal,
        grid_map=grid_map,
        mapping=mapping,
        mission=mission,
        planner=planner,
        motion=motion,
        pose=pose,
        exploration_status=exploration_status,
    )  # CMP--10

    return scheduler, battery


def main():
    scheduler, battery = create_system()
    # Simple blocking loop. In MicroPython this should be the only top-level loop.
    scheduler.run_forever()


if __name__ == "__main__":
    main()

        