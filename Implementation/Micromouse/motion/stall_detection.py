

"""
CMP--9 StallDetectionAndRecovery.

Simplified version:
- Listens to StallDetected from MotionController.
- Emits StallConditionSignal and RecoveryCompletedNotification for exploration controller.
"""

from __future__ import annotations
from typing import Dict, Any

from common.events import EventBus
from common.utils import log


class StallDetectionAndRecovery:
    """Handle stall notifications and publish high-level recovery results."""

    def __init__(self, bus: EventBus, config: Dict[str, Any]) -> None:
        """
        config from ConfigurationManager.get_stall_detection_config()
        """
        self._bus = bus
        self.move_timeout_per_cell_s = config["move_timeout_per_cell_s"]
        self.max_obstacle_retries = config["max_obstacle_retries"]
        self.stall_replan_delay_s = config["stall_replan_delay_s"]

        self._bus.subscribe("StallDetected", self._on_stall_detected)

    def _on_stall_detected(self, info: Dict[str, Any]) -> None:
        """Triggered by MotionController (CMP--5->CMP--9)."""
        log("CMP--9: Stall detected: %r" % (info,))
        # Notify exploration controller via StallConditionSignal
        self._bus.publish("ExplorationStallCondition", info)

        # For now, assume recovery always fails (implementation stub).
        self._bus.publish(
            "RecoveryCompletedNotification", {"success": False}
        )

        