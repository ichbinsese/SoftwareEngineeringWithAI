

"""
Goal Region Identification and Selection.

Traces:
- CMP--5 Goal Region Identification and Selection
"""

from core.types import CELL_FREE


class GoalRegionSelector:
    def __init__(self, grid_map, planner, config):
        self.grid_map = grid_map
        self.planner = planner
        self.config = config
        self.selected_region = None  # dict with 'cells', 'target_cell', 'cost'

    def select_region(self, start_cell):
        """
        Enumerate all 2x2 FREE regions and pick region with minimal path cost
        from start to any of its cells. (CMP--5.Execution)
        """
        best = None
        best_cost = None
        rows = self.grid_map.rows
        cols = self.grid_map.cols
        for r in range(rows - 1):
            for c in range(cols - 1):
                cells = [(r, c), (r + 1, c), (r, c + 1), (r + 1, c + 1)]
                if not all(self.grid_map.get_cell_state(cr, cc) == CELL_FREE for (cr, cc) in cells):
                    continue
                # For each candidate, request path cost using planner
                region_best_cost = None
                region_best_cell = None
                for (cr, cc) in cells:
                    path, cost = self.planner.plan_single(start_cell, (cr, cc), mode="SECOND_RUN")
                    if path:
                        if region_best_cost is None or cost < region_best_cost:
                            region_best_cost = cost
                            region_best_cell = (cr, cc)
                if region_best_cost is None:
                    continue
                if best_cost is None or region_best_cost < best_cost:
                    best_cost = region_best_cost
                    best = {
                        "cells": cells,
                        "target_cell": region_best_cell,
                        "cost": region_best_cost,
                    }
        self.selected_region = best
        return best

        