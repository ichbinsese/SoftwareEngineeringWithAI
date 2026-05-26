

"""
Scheduler and Initialization.

Traces:
- CMP--10 Scheduler and Initialization
"""

import time


class Scheduler:
    def __init__(
        self,
        config,
        sal,
        grid_map,
        mapping,
        mission,
        planner,
        motion,
        pose,
        exploration_status,
    ):
        self.config = config
        self.sal = sal
        self.grid_map = grid_map
        self.mapping = mapping
        self.mission = mission
        self.planner = planner
        self.motion = motion
        self.pose = pose
        self.exploration_status = exploration_status

        self.init_system()

    def init_system(self):
        """Run initialization and set INIT_COMPLETED for mission control. (CMP--10.Execution)"""
        # Grid map already initialized in constructor; pose at start
        self.pose.cell = self.grid_map.start_cell
        # Signal mission control
        self.mission.set_init_completed()

    def run_forever(self):
        """Main control loop at fixed period T. (CMP--10.Execution)"""
        period_s = self.config.control_loop_period_s
        while True:
            start = time.ticks_ms()

            # 1) Emit control loop tick: implicit by calling each module
            # 2) Acquire sensor readings via SAL (CMP--7.Execution)
            self.sal.sample_and_filter()
            sal_data = self.sal.get_filtered()

            # 3) Update mapping (CMP--6.Execution)
            self.mapping.update_from_sensors(self.pose, sal_data)

            # 4) Update exploration status (CMP--11.Execution)
            self.exploration_status.update(start)

            # 5) Update mission control state machine (CMP--1.Execution)
            self.mission.update_mission_time(start)
            self.mission.step()

            # 6) Update pose estimation (CMP--9.Execution)
            self.pose.update(self.motion)

            # 7) Motion control (CMP--8.Execution)
            self.motion.update()

            # Maintain period
            elapsed_ms = time.ticks_ms() - start
            sleep_ms = int(period_s * 1000 - elapsed_ms)
            if sleep_ms > 0:
                time.sleep_ms(sleep_ms)

        