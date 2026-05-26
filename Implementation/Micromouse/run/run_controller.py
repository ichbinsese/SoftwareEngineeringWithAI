

"""
CMP--6 RunController.

Simplified:
- Waits for exploration start and termination events.
- After exploration termination, triggers fastest path computation and (stub) second run.
"""

from __future__ import annotations
from typing import Dict, Any, Optional

from common.events import EventBus
from common.utils import log
from common.types import CellCoord, GridPath
from planning.grid_path_planner import GridPathPlanner
from mapping.map_manager import MapManager
from motion.motion_controller import MotionControllerAndWallAvoidance


class RunController:
    """High-level sequence of runs (explore, return, second run)."""

    def __init__(
        self,
        bus: EventBus,
        planner: GridPathPlanner,
        map_manager: MapManager,
        motion_controller: MotionControllerAndWallAvoidance,
        second_run_cfg: Dict[str, Any],
    ) -> None:
        self._bus = bus
        self._planner = planner
        self._map = map_manager
        self._motion = motion_controller
        self.second_run_cfg = second_run_cfg

        self._state = "RUN_INIT"
        self._fastest_path: Optional[GridPath] = None

        self._bus.subscribe("ExplorationStartEvent", self._on_exploration_start)
        self._bus.subscribe("ExplorationTerminatedEvent", self._on_exploration_terminated)

    def _on_exploration_start(self, payload: Dict[str, Any]) -> None:
        self._state = "EXPLORATION_RUNNING"
        log("CMP--6: Exploration started")

    def _on_exploration_terminated(self, payload: Dict[str, Any]) -> None:
        self._state = "RETURN_TO_START"
        log("CMP--6: Exploration terminated, reason=%s" % payload.get("reason"))

        # Request fastest path to goal
        m = self._map.get_grid_map_and_walls()
        start = CellCoord(0, 0)
        self._fastest_path = self._planner.compute_shortest_path_to_goal_region(m, start)
        if self._fastest_path is None:
            log("CMP--6: No fastest path to goal; skipping second run")
        else:
            log("CMP--6: Fastest path computed, length=%d" % self._fastest_path.length)

        # Return to start from current pose (stub: assume already at start)
        self._state = "WAIT_FOR_FASTEST_PATH"
        # Immediately transition to SECOND_RUN if path exists
        if self._fastest_path:
            self._state = "SECOND_RUN"
            status = self._motion.execute_path(
                self._fastest_path, start_heading=0, second_run=True
            )
            self._state = "RUN_COMPLETE"
            # Notify result evaluator (CMP--10)
            self._bus.publish(
                "SecondRunCompletionNotification",
                {
                    "status": status,
                    "final_cell": {"x": start.x, "y": start.y},  # stub
                },
            )

        