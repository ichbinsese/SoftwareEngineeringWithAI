

"""
Very small synchronous event bus.

This is a lightweight mechanism to connect components as specified
by ConnectedComponents without real concurrency.

Traces:
- Used across CMP--2, CMP--3, CMP--4, CMP--5, CMP--6, CMP--7, CMP--9, CMP--10, CMP--13.
"""

from __future__ import annotations
from typing import Callable, Dict, List, Any


class EventBus:
    """Simple pub/sub bus."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_name: str, cb: Callable[[Any], None]) -> None:
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(cb)

    def publish(self, event_name: str, payload: Any = None) -> None:
        subs = self._subscribers.get(event_name)
        if not subs:
            return
        for cb in subs:
            cb(payload)

        