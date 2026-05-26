

"""
Common enums and simple types.

Traces:
- DAT--1 Grid Map Data Structures
- DAT--2 Traversal Cost Model Parameters
"""

from micropython import const

# --- DAT--1: cell and wall state enums ---
CELL_UNKNOWN = const(0)
CELL_FREE = const(1)
CELL_BLOCKED = const(2)

WALL_UNKNOWN = const(0)
WALL_PRESENT = const(1)
WALL_ABSENT = const(2)

# Mission-related status enums
RETURN_NOT_EXECUTED = const(0)
RETURN_SUCCESS = const(1)
RETURN_FAILURE = const(2)

SECOND_RUN_NOT_EXECUTED = const(0)
SECOND_RUN_SUCCESS = const(1)
SECOND_RUN_FAILURE = const(2)

# Mission states for FSM--1 (CMP--1)
MISSION_IDLE = 0
MISSION_EXPLORE = 1
MISSION_RETURN_TO_START = 2
MISSION_SECOND_RUN = 3
MISSION_COMPLETED = 4

# Simple structure helpers (lightweight since no typing module)
class Cell:
    __slots__ = ("row", "col")
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __iter__(self):
        yield self.row
        yield self.col

    def __repr__(self):
        return "Cell(%d,%d)" % (self.row, self.col)

        