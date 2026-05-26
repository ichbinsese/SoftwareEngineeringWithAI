
# Core data structures for map and paths.
# Trace:
#   - DAT--1 GridMap and Cell structures
#   - DAT--4 GridPath representation

from core.enums import Direction


class OccupancyState:
    UNKNOWN = 0
    FREE = 1
    NON_TRAVERSABLE = 2


class CellWalls:
    def __init__(self):
        # DAT--1 CellWalls
        self.wall_north = False
        self.wall_east = False
        self.wall_south = False
        self.wall_west = False


class Cell:
    def __init__(self):
        # DAT--1 Cell
        self.occupancy = OccupancyState.UNKNOWN
        self.walls = CellWalls()
        self.is_start_region = False
        self.is_goal_region = False
        # Derived metadata
        self.unknown_neighbor_count = 0


class GridMap:
    def __init__(self):
        # DAT--1 GridMap with 4x8 cells
        self.cells = [[Cell() for _ in range(8)] for _ in range(4)]
        self.current_x = 0
        self.current_y = 0
        self.current_heading = Direction.NORTH


class CellCoord:
    # DAT--4 CellCoord
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class GridPath:
    # DAT--4 GridPath
    def __init__(self):
        self.cells = []   # list of CellCoord
        self.moves = []   # list of Direction
        self.length = 0

    def is_empty(self):
        return self.length == 0
