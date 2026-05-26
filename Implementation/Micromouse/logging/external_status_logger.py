

"""
CMP--13 ExternalStatusLogger.

Traces:
- Component CMP--13
"""

from __future__ import annotations
from typing import Dict, Any

from common.events import EventBus
from common.utils import log


class ExternalStatusLogger:
    """Simple console logger for run status."""

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus
        self._bus.subscribe("ExternalRunStatusOutput", self._on_status)

    def _on_status(self, payload: Dict[str, Any]) -> None:
        log("CMP--13: Second run result: %r" % (payload,))

        