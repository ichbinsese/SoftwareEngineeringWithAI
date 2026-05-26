

"""
Event queue infrastructure.

Traces:
- DAT--7 Event Queue for Exploration and Mission Events
- Used by CMP--1 (MissionControl) and CMP--11 (ExplorationStatus)
"""

class EventType:
    EXPLORATION_COMPLETED = 1
    EXPLORATION_TIMEOUT = 2
    PATH_INVALIDATED = 3
    RETURN_COMPLETED = 4
    SECOND_RUN_COMPLETED = 5


class Event:
    __slots__ = ("etype", "timestamp_ms", "payload")
    def __init__(self, etype, timestamp_ms, payload=None):
        self.etype = etype
        self.timestamp_ms = timestamp_ms
        self.payload = payload


class EventQueue:
    """Fixed-size circular buffer event queue. (DAT--7)"""

    def __init__(self, size):
        self._size = size
        self._buf = [None] * size
        self._head = 0
        self._tail = 0
        self._full = False

    def enqueue(self, event):
        if self._full:
            # Drop oldest event
            self._head = (self._head + 1) % self._size
        self._buf[self._tail] = event
        self._tail = (self._tail + 1) % self._size
        self._full = self._tail == self._head

    def dequeue_all(self):
        """Return list of all currently queued events and clear queue."""
        events = []
        while (self._head != self._tail) or self._full:
            events.append(self._buf[self._head])
            self._buf[self._head] = None
            self._head = (self._head + 1) % self._size
            if self._full and self._head == self._tail:
                self._full = False
        return events

        