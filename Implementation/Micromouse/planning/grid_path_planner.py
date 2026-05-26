

"""
CMP--4 GridPathPlanner implementation.

Traces:
- Component CMP--4
- Data DAT--3, DAT--4
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional, Tuple

from common.types import (
    GridMap,
    GridPath,
    CellCoord,
    GRID_WIDTH,
    GRID_HEIGHT,
    DIR_NORTH,
    DIR_EAST,
    DIR_SOUTH,
    DIR_WEST,
    DIRECTION_VECTORS,
    OccupancyState,
)
from common.utils import log


class GridPathPlanner:
    """BFS-based shortest path planner on GridMap."""

    def __init__(self, planner_cfg: Dict[str, Any]) -> None:
        """
        planner_cfg from ConfigurationManager.get_planner_config() (CMP--1->CMP--4).
        """
        self.use_diagonal_moves = planner_cfg.get("use_diagonal_moves", False)
        self.cost_per_step = planner_cfg.get("cost_per_step", 1)

    # ---------- helpers ----------

    def _neighbors(
        self, m: GridMap, x: int, y: int
    ) -> List[Tuple[int, int, int]]:
        res = []
        for direction, (dx, dy) in DIRECTION_VECTORS.items():
            nx = x + dx
            ny = y + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                if self._edge_traversable(m, x, y, nx, ny, direction):
                    res.append((nx, ny, direction))
        return res

    def _edge_traversable(
        self, m: GridMap, x: int, y: int, nx: int, ny: int, direction: int
    ) -> bool:
        cell = m.cells[x][y]
        ncell = m.cells[nx][ny]
        # Wall checks consistent with DAT--2/DAT--3
        if direction == DIR_NORTH:
            if cell.walls.north or ncell.walls.south:
                return False
        elif direction == DIR_SOUTH:
            if cell.walls.south or ncell.walls.north:
                return False
        elif direction == DIR_EAST:
            if cell.walls.east or ncell.walls.west:
                return False
        else:  # WEST
            if cell.walls.west or ncell.walls.east:
                return False

        if (
            cell.occupancy != OccupancyState.FREE
            or ncell.occupancy != OccupancyState.FREE
        ):
            return False
        return True

    # ---------- BFS shortest path (DAT--4) ----------

    def compute_shortest_path(
        self, m: GridMap, start: CellCoord, target: CellCoord
    ) -> Optional[GridPath]:
        """Return minimal-step path or None if no path.

        Implements DAT--4 compute_shortest_path.
        """
        sx, sy = start.x, start.y
        tx, ty = target.x, target.y

        if not (0 <= sx < GRID_WIDTH and 0 <= sy < GRID_HEIGHT):
            return None
        if not (0 <= tx < GRID_WIDTH and 0 <= ty < GRID_HEIGHT):
            return None

        if (
            m.cells[sx][sy].occupancy != OccupancyState.FREE
            or m.cells[tx][ty].occupancy != OccupancyState.FREE
        ):
            return None

        visited = [[False] * GRID_HEIGHT for _ in range(GRID_WIDTH)]
        pred: List[List[Optional[Tuple[int, int]]]] = [
            [None] * GRID_HEIGHT for _ in range(GRID_WIDTH)
        ]
        pred_dir: List[List[int]] = [
            [0] * GRID_HEIGHT for _ in range(GRID_WIDTH)
        ]

        q: List[Tuple[int, int]] = []
        visited[sx][sy] = True
        q.append((sx, sy))

        found = False
        while q:
            x, y = q.pop(0)
            if x == tx and y == ty:
                found = True
                break
            for nx, ny, direction in self._neighbors(m, x, y):
                if not visited[nx][ny]:
                    visited[nx][ny] = True
                    pred[nx][ny] = (x, y)
                    pred_dir[nx][ny] = direction
                    q.append((nx, ny))

        if not found:
            return None

        # Reconstruct path
        path = GridPath()
        cx, cy = tx, ty
        cells_rev: List[CellCoord] = []
        moves_rev: List[int] = []
        while not (cx == sx and cy == sy):
            cells_rev.append(CellCoord(cx, cy))
            d = pred_dir[cx][cy]
            moves_rev.append(d)
            px, py = pred[cx][cy]
            cx, cy = px, py
        cells_rev.append(CellCoord(sx, sy))

        # Reverse
        for coord in reversed(cells_rev):
            path.cells.append(coord)
        for d in reversed(moves_rev):
        # moves[i] moves from cells[i] to cells[i+1]
            path.moves.append(d)

        return path

    # ---------- goal-region planning (DAT--4) ----------

    def compute_shortest_path_to_goal_region(
        self, m: GridMap, start: CellCoord
    ) -> Optional[GridPath]:
        """Find minimal path from start to any goal-region cell."""
        # BFS from start, track distance; record best goal.
        sx, sy = start.x, start.y
        if not (0 <= sx < GRID_WIDTH and 0 <= sy < GRID_HEIGHT):
            return None
        if m.cells[sx][sy].occupancy != OccupancyState.FREE:
            return None

        visited = [[False] * GRID_HEIGHT for _ in range(GRID_WIDTH)]
        pred: List[List[Optional[Tuple[int, int]]]] = [
            [None] * GRID_HEIGHT for _ in range(GRID_WIDTH)
        ]
        pred_dir: List[List[int]] = [
            [0] * GRID_HEIGHT for _ in range(GRID_WIDTH)
        ]

        q: List[Tuple[int, int]] = []
        visited[sx][sy] = True
        q.append((sx, sy))

        goal_cell: Optional[Tuple[int, int]] = None

        while q:
            x, y = q.pop(0)
            cell = m.cells[x][y]
            if cell.is_goal_region and cell.occupancy == OccupancyState.FREE:
                goal_cell = (x, y)
                break
            for nx, ny, direction in self._neighbors(m, x, y):
                if not visited[nx][ny]:
                    visited[nx][ny] = True
                    pred[nx][ny] = (x, y)
                    pred_dir[nx][ny] = direction
                    q.append((nx, ny))

        if goal_cell is None:
            return None

        tx, ty = goal_cell
        # Reconstruct
        path = GridPath()
        cx, cy = tx, ty
        cells_rev: List[CellCoord] = []
        moves_rev: List[int] = []
        while not (cx == sx and cy == sy):
            cells_rev.append(CellCoord(cx, cy))
            d = pred_dir[cx][cy]
            moves_rev.append(d)
            px, py = pred[cx][cy]
            cx, cy = px, py
        cells_rev.append(CellCoord(sx, sy))

        for coord in reversed(cells_rev):
            path.cells.append(coord)
        for d in reversed(moves_rev):
            path.moves.append(d)
        return path

        