

"""
Common types and data structures.

Traces:
- DAT--1: GridMap and Cell definitions
- DAT--4: Direction, CellCoord, GridPath
"""

from __future__ import annotations
from typing import List, Optional, Tuple
from micropython import const


# === Directions and headings (DAT--4, DAT--1) ===

DIR_NORTH = const(0)
DIR_EAST = const(1)
DIR_SOUTH = const(2)
DIR_WEST = const(3)

DIRECTION_VECTORS = {
    DIR_NORTH: (0, 1),
    DIR_EAST: (1, 0),
    DIR_SOUTH: (0, -1),
    DIR_WEST: (-1, 0),
}

DIRECTION_NAMES = {
    DIR_NORTH: "NORTH",
    DIR_EAST: "EAST",
    DIR_SOUTH: "SOUTH",
    DIR_WEST: "WEST",
}


def rotate_left(direction: int) -> int:
    """Rotate heading 90Â° left.

    Trace: used by CMP--3, CMP--5, CMP--9.
    """
    return (direction - 1) & 0x3


def rotate_right(direction: int) -> int:
    """Rotate heading 90Â° right."""
    return (direction + 1) & 0x3


class OccupancyState:
    """Occupancy enumeration (DAT--1)."""

    UNKNOWN = 0
    FREE = 1
    NON_TRAVERSABLE = 2


class CellWalls:
    """Walls around a cell (DAT--1)."""

    __slots__ = ("north", "east", "south", "west")

    def __init__(self) -> None:
        self.north = False
        self.east = False
        self.south = False
        self.west = False


class Cell:
    """Single grid cell (DAT--1)."""

    __slots__ = (
        "occupancy",
        "walls",
        "is_start_region",
        "is_goal_region",
        "unknown_neighbor_count",
    )

    def __init__(self) -> None:
        self.occupancy = OccupancyState.UNKNOWN
        self.walls = CellWalls()
        self.is_start_region = False
        self.is_goal_region = False
        self.unknown_neighbor_count = 0


GRID_WIDTH = const(4)
GRID_HEIGHT = const(8)


class GridMap:
    """4x8 map plus current pose (DAT--1)."""

    __slots__ = ("cells", "current_x", "current_y", "current_heading")

    def __init__(self) -> None:
        self.cells: List[List[Cell]] = [
            [Cell() for _ in range(GRID_HEIGHT)] for _ in range(GRID_WIDTH)
        ]
        self.current_x = 0
        self.current_y = 0
        self.current_heading = DIR_NORTH


class CellCoord:
    """Coordinate in grid (DAT--4)."""

    __slots__ = ("x", "y")

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __iter__(self):
        yield self.x
        yield self.y

    def __repr__(self) -> str:
        return "CellCoord(%d,%d)" % (self.x, self.y)


class GridPath:
    """Path between cells as sequence of moves (DAT--4)."""

    __slots__ = ("cells", "moves")

    def __init__(self) -> None:
        self.cells: List[CellCoord] = []
        self.moves: List[int] = []  # direction step from cells[i] -> cells[i+1]

    @property
    def length(self) -> int:
        return len(self.moves)

    def is_empty(self) -> bool:
        return self.length == 0

        