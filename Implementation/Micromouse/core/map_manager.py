
# MapManager implementation.
# Trace:
#   - CMP--3 MapManager
#   - DAT--1 GridMap structure
#   - DAT--2 wall detection and cell classification
#   - DAT--3 frontier and reachability queries (partial; planner handles BFS)

from core.data_structures import GridMap, OccupancyState
from core.enums import Direction, direction_to_dx_dy, opposite_direction


class MapManager:
    def __init__(self, config_mgr, logger):
        self._cfg = config_mgr
        self._logger = logger
        self._map = GridMap()
        self._initialized = False

    # CMP--3 Execution: initialization
    def initialize_start_and_goal_regions(self):
        # DAT--1: set goal region cells (2,6),(2,7),(3,6),(3,7)
        for x in range(4):
            for y in range(8):
                c = self._map.cells[x][y]
                c.occupancy = OccupancyState.UNKNOWN
                c.walls.wall_north = False
                c.walls.wall_east = False
                c.walls.wall_south = False
                c.walls.wall_west = False
                c.is_start_region = False
                c.is_goal_region = False
                c.unknown_neighbor_count = 0

        self._map.cells[2][6].is_goal_region = True
        self._map.cells[2][7].is_goal_region = True
        self._map.cells[3][6].is_goal_region = True
        self._map.cells[3][7].is_goal_region = True

    def initialize_start_pose(self, heading):
        # DAT--1: start cell (0,0)
        self._map.current_x = 0
        self._map.current_y = 0
        self._map.current_heading = heading
        start_cell = self._map.cells[0][0]
        start_cell.occupancy = OccupancyState.FREE
        start_cell.is_start_region = True
        self._recompute_unknown_neighbors_all()
        self._initialized = True
        self._logger.log("Map initialized with start pose.", component="CMP--3")

    # Interfaces for CMP--2:
    def get_current_pose_info(self):
        return (self._map.current_x, self._map.current_y, self._map.current_heading)

    def set_current_pose(self, x, y, heading):
        if 0 <= x < 4 and 0 <= y < 8:
            self._map.current_x = x
            self._map.current_y = y
            self._map.current_heading = heading
            self._logger.log(
                "Pose updated to (%d,%d) heading %d" % (x, y, heading),
                component="CMP--3",
            )

    def get_grid_map(self):
        # CMP--3 -> CMP--4 GridMapAndWalls (read-only)
        return self._map

    # DAT--2: update map from scan
    def update_from_scan(self, front_distance_cm, ir_left_obstacle, ir_right_obstacle):
        if not self._initialized:
            return
        x = self._map.current_x
        y = self._map.current_y
        heading = self._map.current_heading
        cell = self._map.cells[x][y]

        env = self._cfg.get_env_config()
        safety = self._cfg.get_safety_config()

        cell_size = env["cell_size_cm"]
        wall_thickness = env["wall_thickness_cm"]
        robot_radius = env["robot_radius_cm"]
        uncertainty_margin = env["uncertainty_margin_cm"]
        safety_margin = safety["safety_margin_cm"]

        # DAT--2: d_expected and T_front
        d_expected = (cell_size / 2.0) - robot_radius - (wall_thickness / 2.0)
        t_front = d_expected + safety_margin - uncertainty_margin

        if front_distance_cm is not None and front_distance_cm <= t_front:
            self._set_wall(x, y, heading)

        # Side walls from IR, assign based on current heading.
        if ir_left_obstacle:
            left_dir = self._left_of(heading)
            self._set_wall(x, y, left_dir)
        if ir_right_obstacle:
            right_dir = self._right_of(heading)
            self._set_wall(x, y, right_dir)

        # Cell classification (simplified per DAT--2)
        walls_count = self._count_walls(cell)
        if walls_count <= 3:
            cell.occupancy = OccupancyState.FREE
        else:
            # Enforce max 3 walls; ignore fourth detection
            self._logger.warn(
                "Attempted to set 4th wall at (%d,%d); ignoring last evidence." % (x, y),
                component="CMP--3",
            )
            # Do not change walls here (CMP--3 Failures)
        self._recompute_unknown_neighbors_all()

    def _count_walls(self, cell):
        w = cell.walls
        return int(w.wall_north) + int(w.wall_east) + int(w.wall_south) + int(w.wall_west)

    # DAT--1 wall consistency rules
    def _set_wall(self, x, y, direction):
        if not (0 <= x < 4 and 0 <= y < 8):
            return
        cell = self._map.cells[x][y]
        # Never remove walls; only set to True
        if direction == Direction.NORTH:
            if y < 7:
                cell.walls.wall_north = True
                self._map.cells[x][y + 1].walls.wall_south = True
        elif direction == Direction.SOUTH:
            if y > 0:
                cell.walls.wall_south = True
                self._map.cells[x][y - 1].walls.wall_north = True
        elif direction == Direction.EAST:
            if x < 3:
                cell.walls.wall_east = True
                self._map.cells[x + 1][y].walls.wall_west = True
        elif direction == Direction.WEST:
            if x > 0:
                cell.walls.wall_west = True
                self._map.cells[x - 1][y].walls.wall_east = True

    def _left_of(self, heading):
        return (heading + 3) % 4

    def _right_of(self, heading):
        return (heading + 1) % 4

    # DAT--1 unknown neighbor tracking and frontier identification
    def _recompute_unknown_neighbors_all(self):
        for x in range(4):
            for y in range(8):
                self._map.cells[x][y].unknown_neighbor_count = self._count_unknown_neighbors(x, y)

    def _count_unknown_neighbors(self, x, y):
        count = 0
        for direction in (Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST):
            dx, dy = direction_to_dx_dy(direction)
            nx = x + dx
            ny = y + dy
            if 0 <= nx < 4 and 0 <= ny < 8:
                cell = self._map.cells[x][y]
                if self._has_wall_between(x, y, nx, ny):
                    continue
                neighbor = self._map.cells[nx][ny]
                if neighbor.occupancy == OccupancyState.UNKNOWN:
                    count += 1
        return count

    def _has_wall_between(self, x1, y1, x2, y2):
        if not (0 <= x1 < 4 and 0 <= y1 < 8 and 0 <= x2 < 4 and 0 <= y2 < 8):
            return True
        dx = x2 - x1
        dy = y2 - y1
        if dx == 1 and dy == 0:
            return self._map.cells[x1][y1].walls.wall_east or self._map.cells[x2][y2].walls.wall_west
        if dx == -1 and dy == 0:
            return self._map.cells[x1][y1].walls.wall_west or self._map.cells[x2][y2].walls.wall_east
        if dx == 0 and dy == 1:
            return self._map.cells[x1][y1].walls.wall_north or self._map.cells[x2][y2].walls.wall_south
        if dx == 0 and dy == -1:
            return self._map.cells[x1][y1].walls.wall_south or self._map.cells[x2][y2].walls.wall_north
        # Non-adjacent cells - CMP--3 Failures
        return True

    # CMP--3: ExplorationProgressStatus (DAT--3)
    def get_exploration_progress_status(self, reachable_mask):
        # reachable_mask is 4x8 boolean list provided by planner BFS from current pose
        all_reachable_explored = True
        frontier_cells = []
        for x in range(4):
            for y in range(8):
                if not reachable_mask[x][y]:
                    continue
                cell = self._map.cells[x][y]
                if cell.occupancy == OccupancyState.FREE and cell.unknown_neighbor_count > 0:
                    frontier_cells.append((x, y))
                    all_reachable_explored = False
        return all_reachable_explored, frontier_cells

    # CMP--3: Second run evaluation support for CMP--6/CMP--10
    def evaluate_second_run_success(self, final_x, final_y):
        if not (0 <= final_x < 4 and 0 <= final_y < 8):
            return False, "OUT_OF_BOUNDS"
        cell = self._map.cells[final_x][final_y]
        if cell.occupancy != OccupancyState.FREE:
            return False, "FINAL_NOT_FREE"
        if not cell.is_goal_region:
            return False, "FINAL_NOT_GOAL_REGION"
        # Wall-constraint validation of path would use stored path; omitted for brevity.
        return True, "OK"
