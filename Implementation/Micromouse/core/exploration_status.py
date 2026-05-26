

"""
Exploration Status and Time Limit Module.

Traces:
- CMP--11 Exploration Status and Time Limit Module
"""

from core.events import Event, EventType


class ExplorationStatus:
    def __init__(self, grid_map, config, event_queue):
        self.grid_map = grid_map
        self.config = config
        self.event_queue = event_queue

        self.exploration_started = False
        self.start_time_ms = 0
        self.timeout_emitted = False
        self.completed_emitted = False

        self.elapsed_ms = 0
        self.remaining_ms = self.config.exploration_time_limit_ms

    def on_explore_start(self, mission_time_ms):
        """Called by MissionControl when EXPLORE starts. (CMP--11.Execution)"""
        self.exploration_started = True
        self.start_time_ms = mission_time_ms
        self.timeout_emitted = False
        self.completed_emitted = False

    def on_explore_stop(self):
        """Optional hook when EXPLORE ends."""
        self.exploration_started = False

    def update(self, mission_time_ms):
        """Called once per control loop by Scheduler (CMP--11.Execution)."""
        if not self.exploration_started:
            return

        self.elapsed_ms = mission_time_ms - self.start_time_ms
        if self.elapsed_ms < 0:
            self.elapsed_ms = 0
        if self.elapsed_ms > self.config.exploration_time_limit_ms:
            self.elapsed_ms = self.config.exploration_time_limit_ms

        self.remaining_ms = self.config.exploration_time_limit_ms - self.elapsed_ms
        if self.remaining_ms < 0:
            self.remaining_ms = 0

        # Timeout event (once)
        if (not self.timeout_emitted and
                self.elapsed_ms >= self.config.exploration_time_limit_ms):
            ev = Event(EventType.EXPLORATION_TIMEOUT, mission_time_ms, None)
            self.event_queue.enqueue(ev)
            self.timeout_emitted = True

        # Map completeness event (once)
        if (not self.completed_emitted and self.grid_map.is_complete()):
            ev = Event(EventType.EXPLORATION_COMPLETED, mission_time_ms, None)
            self.event_queue.enqueue(ev)
            self.completed_emitted = True

    def get_remaining_time_info(self):
        """For CMP--1 and CMP--2: RemainingExplorationTimeInfo / TimeAwarePlanningInfo."""
        return self.elapsed_ms, self.remaining_ms

        