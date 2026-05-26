
# ExplorationStateMachineController.
# Trace:
#   - CMP--2 ExplorationStateMachineController
#   - FSM--1 exploration FSM
#
# Simplified implementation: repeatedly scan current cell, update map, select next
# frontier via GridPathPlanner, and command MotionController to execute that path.

from core.enums import Direction
from core.data_structures import CellCoord
from core.timing import monotonic_ms, elapsed_ms


class ExplorationState:
    IDLE = 0
    SCAN_CELL = 1
    UPDATE_MAP = 2
    SELECT_NEXT_TARGET = 3
    MOVE_TO_NEXT_CELL = 4
    RECOVER_FROM_STALL = 5
    TERMINATE = 6


class ExplorationController:
    def __init__(
        self,
        config_mgr,
        map_manager,
        planner,
        sensor_proc,
        motion_ctrl,
        stall_recovery,
        run_controller,
        logger,
    ):
        self._cfg = config_mgr
        self._map_manager = map_manager
        self._planner = planner
        self._sensor = sensor_proc
        self._motion = motion_ctrl
        self._stall = stall_recovery
        self._run_ctrl = run_controller
        self._logger = logger

        self._state = ExplorationState.IDLE
        self._mapping_time_budget_ms = int(self._cfg.get_mapping_time_budget_s() * 1000)
        self._start_time_ms = None
        self._termination_reason = None
        self._pending_path = None

    def request_start(self):
        if self._state == ExplorationState.IDLE:
            self._state = ExplorationState.SCAN_CELL
            self._start_time_ms = monotonic_ms()
            self._logger.log("Exploration started.", component="CMP--2")
            # Notify RunController (FSM--3 RUN_INIT -> EXPLORATION_RUNNING)
            self._run_ctrl.on_exploration_start_event()

    def update(self):
        if self._state == ExplorationState.IDLE:
            return

        # Time budget check
        if (
            self._state != ExplorationState.TERMINATE
            and self._start_time_ms is not None
            and elapsed_ms(self._start_time_ms) >= self._mapping_time_budget_ms
        ):
            self._termination_reason = "TIME_BUDGET_EXCEEDED"
            self._state = ExplorationState.TERMINATE

        if self._state == ExplorationState.SCAN_CELL:
            # FSM--1 SCAN_CELL StateAction
            front, ir_left, ir_right = self._sensor.snapshot_for_cell_scan()
            if front is not None:
                # Assume snapshot is "valid and stable" when non-None
                self._last_scan = (front, ir_left, ir_right)
                self._state = ExplorationState.UPDATE_MAP

        elif self._state == ExplorationState.UPDATE_MAP:
            # FSM--1 UPDATE_MAP StateAction
            if hasattr(self, "_last_scan"):
                front, ir_left, ir_right = self._last_scan
                self._map_manager.update_from_scan(front, ir_left, ir_right)
            self._state = ExplorationState.SELECT_NEXT_TARGET

        elif self._state == ExplorationState.SELECT_NEXT_TARGET:
            # FSM--1 SELECT_NEXT_TARGET StateAction
            frontier, path, all_reachable_explored = self._planner.select_frontier_and_path()
            if all_reachable_explored or frontier is None or path is None:
                self._termination_reason = "MAPPING_COMPLETE"
                self._state = ExplorationState.TERMINATE
            else:
                self._pending_path = path
                self._state = ExplorationState.MOVE_TO_NEXT_CELL
                self._motion.execute_path(path, mode="exploration")

        elif self._state == ExplorationState.MOVE_TO_NEXT_CELL:
            # Monitor motion; MotionController will call back on completion via path exhaustion.
            # Here we approximate completion by checking if motion controller is idle and path cleared.
            if self._motion._current_path is None:
                # Move finished; update pose to last cell in path
                if self._pending_path is not None and self._pending_path.cells:
                    last = self._pending_path.cells[-1]
                    # Heading not tracked precisely; assume unchanged
                    x, y, heading = self._map_manager.get_current_pose_info()
                    self._map_manager.set_current_pose(last.x, last.y, heading)
                self._state = ExplorationState.SCAN_CELL

        elif self._state == ExplorationState.RECOVER_FROM_STALL:
            # Not fully implemented; stall_recovery currently notifies failure immediately.
            self._termination_reason = "FATAL_STALL"
            self._state = ExplorationState.TERMINATE

        elif self._state == ExplorationState.TERMINATE:
            # FSM--1 TERMINATE
            if self._termination_reason is None:
                self._termination_reason = "UNKNOWN"
            self._logger.log(
                "Exploration terminated: %s" % self._termination_reason,
                component="CMP--2",
            )
            # Inform run controller (CMP--6 Event)
            self._run_ctrl.on_exploration_terminated_event(self._termination_reason)
            # Leave in TERMINATE; subsequent calls no-op
            self._state = ExplorationState.IDLE
