
# RunController.
# Trace:
#   - CMP--6 RunController
#   - FSM--3 Run controller FSM

from core.data_structures import CellCoord


class RunState:
    RUN_INIT = 0
    EXPLORATION_RUNNING = 1
    RETURN_TO_START = 2
    WAIT_FOR_FASTEST_PATH = 3
    SECOND_RUN = 4
    RUN_COMPLETE = 5


class RunController:
    def __init__(self, config_mgr, planner, motion_ctrl, map_manager, result_evaluator, logger):
        self._cfg = config_mgr
        self._planner = planner
        self._motion = motion_ctrl
        self._map_manager = map_manager
        self._result_eval = result_evaluator
        self._logger = logger

        self._state = RunState.RUN_INIT
        self._exploration_result = None
        self._run_complete = False
        self._exploration_controller = None

    def set_exploration_controller(self, exploration):
        self._exploration_controller = exploration

    def on_exploration_start_event(self):
        # FSM--3 RUN_INIT -> EXPLORATION_RUNNING
        if self._state == RunState.RUN_INIT:
            self._state = RunState.EXPLORATION_RUNNING
            self._logger.log("RunController: exploration running.", component="CMP--6")

    def on_exploration_terminated_event(self, reason):
        # FSM--3 EXPLORATION_RUNNING -> RETURN_TO_START
        if self._state == RunState.EXPLORATION_RUNNING:
            self._exploration_result = reason
            self._state = RunState.RETURN_TO_START
            self._logger.log(
                "RunController: exploration terminated (%s)." % reason,
                component="CMP--6",
            )

    def update(self):
        if self._state == RunState.RUN_INIT:
            return

        if self._state == RunState.EXPLORATION_RUNNING:
            return

        if self._state == RunState.RETURN_TO_START:
            # Plan and execute return path to (0,0)
            path = self._planner.compute_return_path_to_start()
            if path is None or path.is_empty():
                self._logger.warn(
                    "Return path to start not found; skipping second run.",
                    component="CMP--6",
                )
                self._state = RunState.RUN_COMPLETE
                self._run_complete = True
                return
            self._motion.execute_path(path, mode="return")
            # In this minimal implementation, we assume it completes immediately;
            # in a real system, we would wait for status.
            self._state = RunState.WAIT_FOR_FASTEST_PATH
            # Concurrently request fastest path to goal
            self._planner.compute_fastest_path_to_goal()

        elif self._state == RunState.WAIT_FOR_FASTEST_PATH:
            fastest = self._planner.get_fastest_path()
            if fastest is not None and not fastest.is_empty():
                self._state = RunState.SECOND_RUN
                self._logger.log(
                    "RunController: starting second run.",
                    component="CMP--6",
                )
                # Move robot back to (0,0) logically
                self._map_manager.set_current_pose(0, 0, self._map_manager.get_current_pose_info()[2])
                self._motion.execute_path(fastest, mode="second_run")
            else:
                # Still waiting; nothing to do
                pass

        elif self._state == RunState.SECOND_RUN:
            # Here we approximate completion when motion controller finishes
            if self._motion._current_path is None:
                # Second run finished
                x, y, _ = self._map_manager.get_current_pose_info()
                success, reason = self._map_manager.evaluate_second_run_success(x, y)
                self._result_eval.on_second_run_completed(x, y, success, reason)
                self._state = RunState.RUN_COMPLETE
                self._run_complete = True

        elif self._state == RunState.RUN_COMPLETE:
            # Nothing more to do
            pass

    def is_run_complete(self):
        return self._run_complete
