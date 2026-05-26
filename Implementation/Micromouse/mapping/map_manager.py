

"""
CMP--3 MapManager implementation.

Traces:
- Component CMP--3
- Data DAT--1, DAT--2, DAT--3
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional

from common.types import (
    GridMap,
    Cell,
    CellWalls,
    OccupancyState,
    GRID_WIDTH,
    GRID_HEIGHT,
    DIR_NORTH,
    DIR_EAST,
    DIR_SOUTH,
    DIR_WEST,
    DIRECTION_VECTORS,
    CellCoord,
)
from common.utils import log


class MapManager:
    """4x8 map with walls and frontier logic."""

    def __init__(self, geometry_cfg: Dict[str, Any]) -> None:
        """
        geometry_cfg from ConfigurationManager.get_map_geometry_config() (CMP--1->CMP--3).
        """
        self.map = GridMap()
        self.cell_size_cm = geometry_cfg["cell_size_cm"]
        self.wall_thickness_cm = geometry_cfg["wall_thickness_cm"]
        self.max_walls_per_cell = geometry_cfg["max_walls_per_cell"]
        self._init_map()

    # ---------- initialization (DAT--1) ----------

    def _init_map(self) -> None:
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                c = self.map.cells[x][y]
                c.occupancy = OccupancyState.UNKNOWN
                c.walls = CellWalls()
                c.is_start_region = False
                c.is_goal_region = False
                c.unknown_neighbor_count = 0

        # Start cell (0,0)
        self.map.current_x = 0
        self.map.current_y = 0
        self.map.current_heading = DIR_NORTH
        self._mark_start_region_cell(0, 0)

        # Goal region cells (2,6),(2,7),(3,6),(3,7)
        self._mark_goal_region_cells()

        self._recompute_all_unknown_neighbors()

    # ---------- region marking (CMP--3 ConnectedComponents) ----------

    def _mark_goal_region_cells(self) -> None:
        coords = [(2, 6), (2, 7), (3, 6), (3, 7)]
        for (x, y) in coords:
            if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
                self.map.cells[x][y].is_goal_region = True

    def _mark_start_region_cell(self, x: int, y: int) -> None:
        self.map.cells[x][y].is_start_region = True
        self.map.cells[x][y].occupancy = OccupancyState.FREE

    # API for CMP--2 InitializeStartCellAndHeading
    def initialize_start_cell_and_heading(self, heading: int) -> None:
        self.map.current_x = 0
        self.map.current_y = 0
        self.map.current_heading = heading
        self._mark_start_region_cell(0, 0)
        self._recompute_all_unknown_neighbors()

    # API for CMP--2 SetCurrentPose
    def set_current_pose(self, x: int, y: int, heading: int) -> None:
        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
            log("CMP--3: set_current_pose out of bounds (%d,%d)" % (x, y))
            return
        self.map.current_x = x
        self.map.current_y = y
        self.map.current_heading = heading

    # ---------- wall setting logic (DAT--1, DAT--2) ----------

    def set_wall_at_current_heading_front(self) -> None:
        """Set wall in front of current cell along current heading."""
        self._set_wall(self.map.current_x, self.map.current_y, self.map.current_heading)

    def set_wall_side_left(self) -> None:
        """Set wall at left side of current heading."""
        h = self.map.current_heading
        if h == DIR_NORTH:
            self._set_wall(self.map.current_x, self.map.current_y, DIR_WEST)
        elif h == DIR_EAST:
            self._set_wall(self.map.current_x, self.map.current_y, DIR_NORTH)
        elif h == DIR_SOUTH:
            self._set_wall(self.map.current_x, self.map.current_y, DIR_EAST)
        else:  # WEST
            self._set_wall(self.map.current_x, self.map.current_y, DIR_SOUTH)

    def set_wall_side_right(self) -> None:
        """Set wall at right side of current heading."""
        h = self.map.current_heading
        if h == DIR_NORTH:
            self._set_wall(self.map.current_x, self.map.current_y, DIR_EAST)
        elif h == DIR_EAST:
            self._set_wall(self.map.current_x, self.map.current_y, DIR_SOUTH)
        elif h == DIR_SOUTH:
            self._set_wall(self.map.current_x, self.map.current_y, DIR_WEST)
        else:  # WEST
            self._set_wall(self.map.current_x, self.map.current_y, DIR_NORTH)

    def _set_wall(self, x: int, y: int, direction: int) -> None:
        """Apply wall consistency rules (DAT--1)."""
        if not (0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT):
            log("CMP--3: attempt to set wall out of bounds (%d,%d)" % (x, y))
            return

        cell = self.map.cells[x][y]

        # Check max walls per cell
        wall_count = (
            cell.walls.north
            + cell.walls.east
            + cell.walls.south
            + cell.walls.west
        )
        if wall_count >= self.max_walls_per_cell:
            # Per DAT--2, ignore sensor evidence suggesting a 4th wall
            log("CMP--3: ignoring 4th wall evidence at (%d,%d)" % (x, y))
            return

        dx, dy = DIRECTION_VECTORS[direction]
        nx = x + dx
        ny = y + dy

        # Determine primary and neighbor wall attributes
        if direction == DIR_NORTH:
            cell.walls.north = True
            if ny < GRID_HEIGHT:
                ncell = self.map.cells[nx][ny]
                ncell.walls.south = True
        elif direction == DIR_SOUTH:
            cell.walls.south = True
            if ny >= 0:
                ncell = self.map.cells[nx][ny]
                ncell.walls.north = True
        elif direction == DIR_EAST:
            cell.walls.east = True
            if nx < GRID_WIDTH:
                ncell = self.map.cells[nx][ny]
                ncell.walls.west = True
        else:  # WEST
            cell.walls.west = True
            if nx >= 0:
                ncell = self.map.cells[nx][ny]
                ncell.walls.east = True

        self._recompute_unknown_neighbors_around(x, y)

    # ---------- cell classification and update from scan (DAT--2) ----------

    def update_from_scan(
        self,
        current_x: int,
        current_y: int,
        current_heading: int,
        front_distance_cm_filtered: Optional[float],
        ir_left_obstacle: bool,
        ir_right_obstacle: bool,
        safety_margin_cm: float,
        robot_radius_cm: float,
        uncertainty_margin_cm: float,
    ) -> None:
        """Apply CellScanSensorData to walls and cell occupancy.

        Parameters trace back to:
        - CMP--2/3 MapUpdateFromScan
        - DAT--2 wall detection logic
        """
        if not (0 <= current_x < GRID_WIDTH and 0 <= current_y < GRID_HEIGHT):
            log("CMP--3: update_from_scan out of bounds")
            return

        self.map.current_x = current_x
        self.map.current_y = current_y
        self.map.current_heading = current_heading

        cell = self.map.cells[current_x][current_y]

        # Wall detection from ultrasonic (front) (DAT--2)
        if front_distance_cm_filtered is not None:
            d_expected = (
                self.cell_size_cm / 2.0
                - robot_radius_cm
                - self.wall_thickness_cm / 2.0
            )
            t_front = d_expected + safety_margin_cm - uncertainty_margin_cm
            if front_distance_cm_filtered <= t_front:
                self.set_wall_at_current_heading_front()

        # IR-based side walls (DAT--2)
        if ir_left_obstacle:
            self.set_wall_side_left()
        if ir_right_obstacle:
            self.set_wall_side_right()

        # Cell classification (simplified rule from DAT--2)
        cell.occupancy = OccupancyState.FREE

        self._recompute_unknown_neighbors_around(current_x, current_y)

    # ---------- unknown neighbor counting & frontier (DAT--1, DAT--3) ----------

    def _neighbors(self, x: int, y: int) -> List[Tuple[int, int, int]]:
        res = []
        for direction, (dx, dy) in DIRECTION_VECTORS.items():
            nx = x + dx
            ny = y + dy
            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                res.append((nx, ny, direction))
        return res

    def _recompute_unknown_neighbors_around(self, x: int, y: int) -> None:
        # Recompute for cell (x,y) and all neighbors (DAT--1)
        for (cx, cy) in [(x, y)] + [(nx, ny) for (nx, ny, _) in self._neighbors(x, y)]:
            self._recompute_unknown_neighbors_for_cell(cx, cy)

    def _recompute_unknown_neighbors_for_cell(self, x: int, y: int) -> None:
        cell = self.map.cells[x][y]
        count = 0
        for nx, ny, direction in self._neighbors(x, y):
            ncell = self.map.cells[nx][ny]
            if ncell.occupancy == OccupancyState.UNKNOWN and self._edge_traversable(
                x, y, nx, ny, direction
            ):
                count += 1
        cell.unknown_neighbor_count = count

    def _recompute_all_unknown_neighbors(self) -> None:
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                self._recompute_unknown_neighbors_for_cell(x, y)

    def _edge_traversable(
        self, x: int, y: int, nx: int, ny: int, direction: int
    ) -> bool:
        cell = self.map.cells[x][y]
        ncell = self.map.cells[nx][ny]
        # Check walls consistent with DAT--2, DAT--3
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
        # Non-traversable occupancy
        if (
            cell.occupancy == OccupancyState.NON_TRAVERSABLE
            or ncell.occupancy == OccupancyState.NON_TRAVERSABLE
        ):
            return False
        return True

    # ---------- ExplorationProgressStatus (DAT--3, CMP--2->CMP--3) ----------

    def compute_exploration_progress_status(
        self,
    ) -> Dict[str, Any]:
        """Return all_reachable_explored and frontier cells.

        Implementation per DAT--3 using reachable-cell semantics LL-PLAN-1.1.6.
        """
        start = (self.map.current_x, self.map.current_y)
        reachable_free = self._bfs_reachable_free(start)
        frontier_cells = []

        for (x, y) in reachable_free:
            cell = self.map.cells[x][y]
            if (
                cell.occupancy == OccupancyState.FREE
                and cell.unknown_neighbor_count > 0
            ):
                frontier_cells.append({"x": x, "y": y})

        all_reachable_explored = len(frontier_cells) == 0
        return {
            "all_reachable_explored": all_reachable_explored,
            "frontier_cells": frontier_cells,
        }

    def _bfs_reachable_free(self, start: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Return all free cells reachable from start (DAT--3)."""
        sx, sy = start
        visited = [[False] * GRID_HEIGHT for _ in range(GRID_WIDTH)]
        q: List[Tuple[int, int]] = []
        if not (0 <= sx < GRID_WIDTH and 0 <= sy < GRID_HEIGHT):
            return []
        if self.map.cells[sx][sy].occupancy != OccupancyState.FREE:
            return []

        visited[sx][sy] = True
        q.append((sx, sy))
        res: List[Tuple[int, int]] = []

        while q:
            x, y = q.pop(0)
            res.append((x, y))
            for nx, ny, direction in self._neighbors(x, y):
                if visited[nx][ny]:
                    continue
                ncell = self.map.cells[nx][ny]
                if ncell.occupancy != OccupancyState.FREE:
                    continue
                if not self._edge_traversable(x, y, nx, ny, direction):
                    continue
                visited[nx][ny] = True
                q.append((nx, ny))
        return res

    # ---------- API for GridPathPlanner (CMP--3->CMP--4) ----------

    def get_grid_map_and_walls(self) -> GridMap:
        """Return reference to internal map (read-only by convention)."""
        return self.map

    # ---------- Second run evaluation (CMP--3<->CMP--6/CMP--10) ----------

    def evaluate_second_run_success(self, final_x: int, final_y: int) -> Dict[str, Any]:
        """Check final pose is free, in goal region, and within map.

        Trace:
        - CMP--3: SecondRunSuccessEvaluationResult
        - DAT--1, DAT--3 invariants
        """
        success = True
        reasons = []

        if not (0 <= final_x < GRID_WIDTH and 0 <= final_y < GRID_HEIGHT):
            success = False
            reasons.append("OUT_OF_BOUNDS")
        else:
            cell = self.map.cells[final_x][final_y]
            if cell.occupancy != OccupancyState.FREE:
                success = False
                reasons.append("FINAL_CELL_NOT_FREE")
            if not cell.is_goal_region:
                success = False
                reasons.append("FINAL_CELL_NOT_GOAL_REGION")

        # For simplicity, assume any path executed by MotionController
        # respects wall constraints by design (CMP--5 invariants).
        return {"success": success, "reasons": reasons}

        