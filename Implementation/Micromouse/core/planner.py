

"""
Path Planner.

Traces:
- CMP--4 Path Planner
- DAT--2 Traversal Cost Model Parameters
"""

from core.types import CELL_FREE, CELL_BLOCKED
from core.types import WALL_PRESENT


class PathPlanner:
    def __init__(self, grid_map, config):
        self.grid_map = grid_map
        self.config = config

    # --- Core graph helpers ---

    def _neighbors_free(self, cell):
        """Return neighboring FREE cells with no PRESENT wall between them."""
        (r, c) = cell
        res = []
        for (nr, nc) in self.grid_map.get_neighbors4(r, c):
            if self.grid_map.get_cell_state(nr, nc) != CELL_FREE:
                continue
            if self.grid_map.get_wall_state_between(r, c, nr, nc) == WALL_PRESENT:
                continue
            res.append((nr, nc))
        return res

    def _heuristic(self, a, b):
        """Manhattan heuristic for A* (CMP--4.Execution)."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _edge_cost(self, prev, cur, nxt, mode):
        """
        Cost according to DAT--2:
        - baseStraightCost
        - turnPenalty when direction changes
        """
        if mode == "SECOND_RUN":
            base = self.config.second_run_straight_cost
            turn_penalty = self.config.second_run_turn_penalty
        else:
            base = self.config.exploration_straight_cost
            turn_penalty = self.config.exploration_turn_penalty

        if prev is None or cur is None or nxt is None:
            return base
        dr1 = cur[0] - prev[0]
        dc1 = cur[1] - prev[1]
        dr2 = nxt[0] - cur[0]
        dc2 = nxt[1] - cur[1]
        if dr1 == dr2 and dc1 == dc2:
            return base
        return base + turn_penalty

    # --- Public planning API (CMP--4.ConnectedComponents) ---

    def plan_single(self, start, goal, mode="EXPLORE", max_cost=None):
        """
        Plan path from start to single goal cell using A*.
        Returns (path:list[(r,c)], total_cost) or (None, None).
        """
        if self.grid_map.get_cell_state(start[0], start[1]) == CELL_BLOCKED:
            return None, None
        if self.grid_map.get_cell_state(goal[0], goal[1]) == CELL_BLOCKED:
            return None, None

        open_set = [start]
        came_from = {}
        g_score = {start: 0.0}
        f_score = {start: self._heuristic(start, goal)}

        while open_set:
            # Find node with smallest f
            current = None
            best_f = None
            for n in open_set:
                f = f_score.get(n, 1e9)
                if best_f is None or f < best_f:
                    best_f = f
                    current = n

            if current == goal:
                return self._reconstruct_path(came_from, current), g_score[current]

            open_set.remove(current)
            neighbors = self._neighbors_free(current)
            for neighbor in neighbors:
                prev = came_from.get(current, None)
                tentative_g = g_score[current] + self._edge_cost(prev, current, neighbor, mode)
                if max_cost is not None and tentative_g > max_cost:
                    continue
                if tentative_g < g_score.get(neighbor, 1e9):
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self._heuristic(neighbor, goal)
                    if neighbor not in open_set:
                        open_set.append(neighbor)
        return None, None

    def _reconstruct_path(self, came_from, current):
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path

        