

"""
CMP--10 SecondRunResultEvaluatorAndReporter.

Simplified:
- Receives SecondRunCompletionNotification from RunController.
- Asks MapManager for success evaluation.
- Publishes SecondRunResult and logs via ExternalStatusLogger.
"""

from __future__ import annotations
from typing import Dict, Any

from common.events import EventBus
from common.utils import log
from mapping.map_manager import MapManager


class SecondRunResultEvaluatorAndReporter:
    """Evaluate second run success and report."""

    def __init__(self, bus: EventBus, map_manager: MapManager) -> None:
        self._bus = bus
        self._map = map_manager

        self._bus.subscribe(
            "SecondRunCompletionNotification", self._on_second_run_completed
        )

    def _on_second_run_completed(self, payload: Dict[str, Any]) -> None:
        """Handle second run completion (CMP--10)."""
        final_cell = payload.get("final_cell", {"x": 0, "y": 0})
        x = int(final_cell["x"])
        y = int(final_cell["y"])
        eval_res = self._map.evaluate_second_run_success(x, y)
        success = eval_res["success"]
        reasons = eval_res["reasons"]

        result = {
            "success": success,
            "reasons": reasons,
        }
        # Notify RunController / others
        self._bus.publish("SecondRunResult", result)
        # Log externally (CMP--13)
        self._bus.publish("ExternalRunStatusOutput", result)

        