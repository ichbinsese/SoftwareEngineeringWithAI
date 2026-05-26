

"""
Frontier Generation and Target Selection.

Traces:
- CMP--2 Frontier Generation and Exploration Target Selection
- Uses DAT--3 Time-Aware Planning
"""

from core.types import CELL_UNKNOWN, CELL_FREE


class FrontierGenerator:
    def __init__(self, grid_map, planner, config):
        self.grid_map = grid_map
        self.planner = planner
        self.config = config

    def compute_frontiers(self):
        """Compute frontier cells (CMP--2.Purpose)."""
        frontiers = []
        for r in range(self.grid_map.rows):
            for c in range(self.grid_map.cols):
                if self.grid_map.get_cell_state(r, c) != CELL_UNKNOWN:
                    continue
                # Must have at least one FREE 4-neighbor
                neighbors = self.grid_map.get_neighbors4(r, c)
                has_free = any(self.grid_map.get_cell_state(nr, nc) == CELL_FREE for (nr, nc) in neighbors)
                if has_free:
                    frontiers.append((r, c))
        return frontiers

    def select_target(self, current_cell, remaining_time_ms):
        """
        Select single frontier target using a simple heuristic:
        - Feasible given remaining_time_ms (DAT--3 frontier feasibility test).
        - Minimizes path cost (CMP--2.Purpose).
        Returns dict or None.
        """
        frontiers = self.compute_frontiers()
        if not frontiers:
            return None

        best = None
        best_cost = None
        for (fr, fc) in frontiers:
            path, cost = self.planner.plan_single(
                start=current_cell,
                goal=(fr, fc),
                mode="EXPLORE",
                max_cost=None,
            )
            if not path:
                continue
            # Estimate travel time (simplistic: steps * nominal per cell)
            steps = len(path) - 1
            est_travel_ms = steps * self.config.nominal_cell_traversal_ms
            est_mapping_overhead_ms = self.config.nominal_cell_traversal_ms
            if est_travel_ms + est_mapping_overhead_ms > remaining_time_ms:
                continue
            if best_cost is None or cost < best_cost:
                best_cost = cost
                best = {
                    "target_cell": (fr, fc),
                    "path": path,
                    "cost": cost,
                    "est_travel_ms": est_travel_ms,
                }
        return best

        