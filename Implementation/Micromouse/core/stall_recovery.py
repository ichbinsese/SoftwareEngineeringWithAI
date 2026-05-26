
# StallDetectionAndRecovery.
# Trace:
#   - CMP--9 StallDetectionAndRecovery
#   - Receives stall notifications from CMP--5
#   - Uses CMP--3 and CMP--4 for local topology and optional replanning

from core.enums import Direction
from core.timing import monotonic_ms


class StallDetectionAndRecovery:
    def __init__(self, config_mgr, map_manager, planner, motion_ctrl, logger):
        self._cfg = config_mgr
        self._map_manager = map_manager
        self._planner = planner
        self._motion_ctrl = motion_ctrl
        self._logger = logger
        self._active = False
        self._last_stall_time_ms = 0

    # Called by MotionController when stall detected (CMP--9 ConnectedComponents)
    def on_stall_detected(self, reason):
        self._logger.warn("StallRecovery: stall detected (%s)" % reason, component="CMP--9")
        self._active = True
        self._last_stall_time_ms = monotonic_ms()
        # Simple recovery: attempt small back-and-forth using MotorAbstraction via MotionController?
        # For now, just notify motion controller that recovery is "done" and let higher-level planner re-choose path.
        self._motion_ctrl.on_recovery_completed(success=False)
        self._active = False

    # In more advanced version, this module would construct a StallRecoveryPlan path
    # of local moves and instruct MotionController to execute them, then notify CMP--2.
