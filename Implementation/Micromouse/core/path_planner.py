
# GridPathPlanner implementation.
# Trace:
#   - CMP--4 GridPathPlanner
#   - DAT--3 frontier selection uses same BFS
#   - DAT--4 BFS-based shortest path

from core.data_structures import GridPath, CellCoord, OccupancyState
from core.enums import Direction, direction_to_dx_dy


class GridPathPlanner:
    def __init__(self, map_manager, config_mgr, logger):
        self._map_manager = map_manager
        self._cfg = config_mgr
        self._logger = logger
        self._fastest_path = None  # CMP--4: stored fastest path after exploration

    # DAT--4: BFS shortest path
    def compute_shortest_path(self, start, target):
        grid = self._map_manager.get_grid_map()
        width = 4
        height = 8

        visited = [[False for _ in range(height)] for _ in range(width)]
        pred = [[None for _ in range(height)] for _ in range(width)]

        queue = []
        sx, sy = start.x, start.y
        tx, ty = target.x, target.y

        if not (0 <= sx < width and 0 <= sy < height and 0 <= tx < width and 0 <= ty < height):
            return None

        start_cell = grid.cells[sx][sy]
        target_cell = grid.cells[tx][ty]
        if start_cell.occupancy != OccupancyState.FREE or target_cell.occupancy != OccupancyState.FREE:
            return None

        visited[sx][sy] = True
        queue.append((sx, sy))

        while queue:
            x, y = queue.pop(0)
            if x == tx and y == ty:
                break
            for direction in (Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST):
                dx, dy = direction_to_dx_dy(direction)
                nx = x + dx
                ny = y + dy
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                if visited[nx][ny]:
                    continue
                if self._has_wall_between(grid, x, y, nx, ny):
                    continue
                neighbor_cell = grid.cells[nx][ny]
                if neighbor_cell.occupancy != OccupancyState.FREE:
                    continue
                visited[nx][ny] = True
                pred[nx][ny] = (x, y)
                queue.append((nx, ny))

        if not visited[tx][ty]:
            return None

        # Reconstruct path
        path_cells = []
        cx, cy = tx, ty
        while not (cx == sx and cy == sy):
            path_cells.append((cx, cy))
            cx, cy = pred[cx][cy]
        path_cells.append((sx, sy))
        path_cells.reverse()

        grid_path = GridPath()
        for (x, y) in path_cells:
            grid_path.cells.append(CellCoord(x, y))

        # Derive moves
        for i in range(len(grid_path.cells) - 1):
            c0 = grid_path.cells[i]
            c1 = grid_path.cells[i + 1]
            dx = c1.x - c0.x
            dy = c1.y - c0.y
            if dx == 1 and dy == 0:
                grid_path.moves.append(Direction.EAST)
            elif dx == -1 and dy == 0:
                grid_path.moves.append(Direction.WEST)
            elif dx == 0 and dy == 1:
                grid_path.moves.append(Direction.NORTH)
            elif dx == 0 and dy == -1:
                grid_path.moves.append(Direction.SOUTH)
            else:
                # Should not happen for valid grid neighbors
                grid_path.moves.append(Direction.NORTH)
        grid_path.length = len(grid_path.moves)
        return grid_path

    def _has_wall_between(self, grid, x1, y1, x2, y2):
        # DAT--4: wall constraints for BFS neighbor expansion
        if not (0 <= x1 < 4 and 0 <= y1 < 8 and 0 <= x2 < 4 and 0 <= y2 < 8):
            return True
        dx = x2 - x1
        dy = y2 - y1
        c1 = grid.cells[x1][y1]
        c2 = grid.cells[x2][y2]
        if dx == 1 and dy == 0:
            return c1.walls.wall_east or c2.walls.wall_west
        if dx == -1 and dy == 0:
            return c1.walls.wall_west or c2.walls.wall_east
        if dx == 0 and dy == 1:
            return c1.walls.wall_north or c2.walls.wall_south
        if dx == 0 and dy == -1:
            return c1.walls.wall_south or c2.walls.wall_north
        return True

    # Helper to compute reachability mask from a start cell (DAT--3)
    def compute_reachability_mask(self, start):
        grid = self._map_manager.get_grid_map()
        width = 4
        height = 8
        visited = [[False for _ in range(height)] for _ in range(width)]
        queue = []

        sx, sy = start.x, start.y
        if not (0 <= sx < width and 0 <= sy < height):
            return visited

        queue.append((sx, sy))
        visited[sx][sy] = True

        while queue:
            x, y = queue.pop(0)
            for direction in (Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST):
                dx, dy = direction_to_dx_dy(direction)
                nx = x + dx
                ny = y + dy
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                if visited[nx][ny]:
                    continue
                if self._has_wall_between(grid, x, y, nx, ny):
                    continue
                cell = grid.cells[nx][ny]
                if cell.occupancy != OccupancyState.FREE:
                    continue
                visited[nx][ny] = True
                queue.append((nx, ny))

        return visited

    # DAT--3: frontier target selection using BFS
    def select_frontier_and_path(self):
        # Determine reachable frontier cells from current pose
        x, y, _ = self._map_manager.get_current_pose_info()
        start = CellCoord(x, y)
        reachable = self.compute_reachability_mask(start)
        all_reachable_explored, frontiers = self._map_manager.get_exploration_progress_status(
            reachable
        )
        if all_reachable_explored or not frontiers:
            return None, None, all_reachable_explored

        best_path = None
        best_frontier = None

        for (fx, fy) in frontiers:
            path = self.compute_shortest_path(start, CellCoord(fx, fy))
            if path is None:
                continue
            if best_path is None or path.length < best_path.length:
                best_path = path
                best_frontier = (fx, fy)

        return best_frontier, best_path, all_reachable_explored

    # CMP--4: Return path planning to (0,0)
    def compute_return_path_to_start(self):
        x, y, _ = self._map_manager.get_current_pose_info()
        start = CellCoord(x, y)
        target = CellCoord(0, 0)
        return self.compute_shortest_path(start, target)

    # CMP--4: Fastest path to goal region after exploration
    def compute_fastest_path_to_goal(self):
        grid = self._map_manager.get_grid_map()
        sx, sy, _ = self._map_manager.get_current_pose_info()
        start = CellCoord(sx, sy)

        # BFS from start, track distance and predecessor
        width = 4
        height = 8
        visited = [[False for _ in range(height)] for _ in range(width)]
        pred = [[None for _ in range(height)] for _ in range(width)]
        dist = [[9999 for _ in range(height)] for _ in range(width)]

        queue = []
        queue.append((sx, sy))
        visited[sx][sy] = True
        dist[sx][sy] = 0

        goals = []

        while queue:
            x, y = queue.pop(0)
            cell = grid.cells[x][y]
            if cell.is_goal_region and cell.occupancy == OccupancyState.FREE:
                goals.append((x, y))
            for direction in (Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST):
                dx, dy = direction_to_dx_dy(direction)
                nx = x + dx
                ny = y + dy
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                if visited[nx][ny]:
                    continue
                if self._has_wall_between(grid, x, y, nx, ny):
                    continue
                neighbor = grid.cells[nx][ny]
                if neighbor.occupancy != OccupancyState.FREE:
                    continue
                visited[nx][ny] = True
                dist[nx][ny] = dist[x][y] + 1
                pred[nx][ny] = (x, y)
                queue.append((nx, ny))

        if not goals:
            self._fastest_path = None
            self._logger.warn("No goal-region path found.", component="CMP--4")
            return None

        # Pick closest goal
        best_goal = None
        best_d = 9999
        for (gx, gy) in goals:
            if dist[gx][gy] < best_d:
                best_d = dist[gx][gy]
                best_goal = (gx, gy)

        target = CellCoord(best_goal[0], best_goal[1])
        path = self.compute_shortest_path(start, target)
        self._fastest_path = path
        self._logger.log("Fastest path to goal computed.", component="CMP--4")
        return path

    def get_fastest_path(self):
        return self._fastest_path
