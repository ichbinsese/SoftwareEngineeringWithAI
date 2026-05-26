

"""
Grid Map Module.

Traces:
- CMP--3 Grid Map Module
- DAT--1 Grid Map Data Structures
"""

from core.types import CELL_UNKNOWN, CELL_FREE, CELL_BLOCKED
from core.types import WALL_UNKNOWN, WALL_PRESENT, WALL_ABSENT


class GridMap:
    """4x8 grid map with cell and wall classifications. (CMP--3, DAT--1)"""

    def __init__(self, config):
        self.config = config
        self.rows = config.rows
        self.cols = config.cols

        # DAT--1: cell and wall storage
        self.cells = [[CELL_UNKNOWN for _ in range(self.cols)] for _ in range(self.rows)]
        # Horizontal walls: between (row, col) and (row+1, col) => 3 x 8
        self.h_walls = [[WALL_UNKNOWN for _ in range(self.cols)] for _ in range(self.rows - 1)]
        # Vertical walls: between (row, col) and (row, col+1) => 4 x 7
        self.v_walls = [[WALL_UNKNOWN for _ in range(self.cols - 1)] for _ in range(self.rows)]

        self.unknown_cells_count = self.rows * self.cols
        # Approximate wall count: horizontal + vertical
        self.unknown_walls_count = (self.rows - 1) * self.cols + self.rows * (self.cols - 1)
        self.map_complete = False

        self.start_cell = (0, 0)

        self.init_map()

    # --- Initialization (CMP--3.Execution #1) ---

    def init_map(self):
        """Initialize cells and walls to UNKNOWN and start cell FREE."""
        for r in range(self.rows):
            for c in range(self.cols):
                self.cells[r][c] = CELL_UNKNOWN
        for r in range(self.rows - 1):
            for c in range(self.cols):
                self.h_walls[r][c] = WALL_UNKNOWN
        for r in range(self.rows):
            for c in range(self.cols - 1):
                self.v_walls[r][c] = WALL_UNKNOWN
        self.unknown_cells_count = self.rows * self.cols
        self.unknown_walls_count = (self.rows - 1) * self.cols + self.rows * (self.cols - 1)
        # Start cell FREE (CMP--3.Execution)
        sr, sc = self.start_cell
        self._set_cell_state(sr, sc, CELL_FREE)

    # --- Queries (CMP--3.Purpose) ---

    def in_bounds(self, row, col):
        return 0 <= row < self.rows and 0 <= col < self.cols

    def get_cell_state(self, row, col):
        if not self.in_bounds(row, col):
            return CELL_BLOCKED  # treat out-of-bounds as blocked
        return self.cells[row][col]

    def get_neighbors4(self, row, col):
        """Return list of in-bounds orthogonal neighbors (no wall consideration)."""
        res = []
        if row > 0:
            res.append((row - 1, col))
        if row < self.rows - 1:
            res.append((row + 1, col))
        if col > 0:
            res.append((row, col - 1))
        if col < self.cols - 1:
            res.append((row, col + 1))
        return res

    def _wall_index(self, row, col, nrow, ncol):
        """Return (orientation, r, c) for wall between (row,col) and (nrow,ncol)."""
        if row == nrow:
            # vertical wall between cols
            c = min(col, ncol)
            return ("V", row, c)
        elif col == ncol:
            # horizontal wall between rows
            r = min(row, nrow)
            return ("H", r, col)
        else:
            return (None, None, None)

    def get_wall_state_between(self, row, col, nrow, ncol):
        orient, r, c = self._wall_index(row, col, nrow, ncol)
        if orient is None:
            return WALL_PRESENT
        if orient == "H":
            return self.h_walls[r][c]
        else:
            return self.v_walls[r][c]

    # --- Updates enforcing invariants (CMP--3.Invariants) ---

    def _set_cell_state(self, row, col, new_state):
        """Internal: enforce UNKNOWN->FREE/BLOCKED only."""
        if not self.in_bounds(row, col):
            return
        old = self.cells[row][col]
        if old == new_state:
            return
        if old != CELL_UNKNOWN:
            # Invalid transition: ignore per CMP--3.Failures
            return
        if new_state not in (CELL_FREE, CELL_BLOCKED):
            return
        self.cells[row][col] = new_state
        self.unknown_cells_count -= 1
        self._update_map_completeness()

    def set_cell_free(self, row, col):
        self._set_cell_state(row, col, CELL_FREE)

    def set_cell_blocked(self, row, col):
        self._set_cell_state(row, col, CELL_BLOCKED)

    def _set_wall_state(self, orient, r, c, new_state):
        """Internal: enforce UNKNOWN->PRESENT/ABSENT only."""
        if orient == "H":
            if not (0 <= r < self.rows - 1 and 0 <= c < self.cols):
                return
            old = self.h_walls[r][c]
            if old != WALL_UNKNOWN or new_state not in (WALL_PRESENT, WALL_ABSENT):
                return
            self.h_walls[r][c] = new_state
        else:
            if not (0 <= r < self.rows and 0 <= c < self.cols - 1):
                return
            old = self.v_walls[r][c]
            if old != WALL_UNKNOWN or new_state not in (WALL_PRESENT, WALL_ABSENT):
                return
            self.v_walls[r][c] = new_state
        self.unknown_walls_count -= 1
        self._update_map_completeness()

    def set_wall_present_between(self, row, col, nrow, ncol):
        orient, r, c = self._wall_index(row, col, nrow, ncol)
        if orient is None:
            return
        self._set_wall_state(orient, r, c, WALL_PRESENT)

    def set_wall_absent_between(self, row, col, nrow, ncol):
        orient, r, c = self._wall_index(row, col, nrow, ncol)
        if orient is None:
            return
        self._set_wall_state(orient, r, c, WALL_ABSENT)

    def _update_map_completeness(self):
        """Maintain GM_MapCompletenessFlag (CMP--3.Execution #6)."""
        self.map_complete = (self.unknown_cells_count == 0 and self.unknown_walls_count == 0)

    def is_complete(self):
        return self.map_complete

        