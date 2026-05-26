

"""
Mapping and Wall Detection Module.

Traces:
- CMP--6 Mapping and Wall Detection Module
- DAT--4 Ultrasonic Uncertainty and Clearance Checks
- DAT--5 Sensor Filtering and Consistency Parameters
"""

from core.types import CELL_UNKNOWN, CELL_FREE, CELL_BLOCKED
from core.types import WALL_UNKNOWN, WALL_PRESENT, WALL_ABSENT


class MappingModule:
    def __init__(self, grid_map, config):
        self.grid_map = grid_map
        self.config = config

    def update_from_sensors(self, pose, sal_data):
        """
        Apply simple mapping rules based on filtered sensors and pose.
        This is a simplified version focusing on:
        - front wall detection using ultrasonic
        - free cell confirmation when pose at cell center
        Traces CMP--6.Execution steps 1,2,3 partially.
        """
        if sal_data is None:
            return

        # Free cell confirmation: mark current cell FREE if UNKNOWN
        cr, cc = pose.cell
        if self.grid_map.get_cell_state(cr, cc) == CELL_UNKNOWN:
            self.grid_map.set_cell_free(cr, cc)

        # Front wall detection using ultrasonic (DAT--4)
        d_cm = sal_data["ultra_cm"]
        if d_cm is None:
            return
        # Expand reading
        d_min = d_cm - self.config.ultrasonic_uncertainty_cm
        d_max = d_cm + self.config.ultrasonic_uncertainty_cm
        # Expected center-to-wall distance for front wall (approx)
        approx = (self.config.cell_size_cm / 2.0) + (self.config.wall_thickness_cm / 2.0)
        # If intervals intersect, mark wall PRESENT in heading direction
        if d_min <= approx <= d_max:
            self._set_front_wall_present(pose)

    def _set_front_wall_present(self, pose):
        """Mark wall PRESENT in front of current cell; infer neighbor BLOCKED if UNKNOWN."""
        cr, cc = pose.cell
        heading = pose.heading  # 0:N,1:E,2:S,3:W
        nr, nc = cr, cc
        if heading == 0:  # NORTH -> row-1
            nr = cr - 1
        elif heading == 1:  # EAST
            nc = cc + 1
        elif heading == 2:  # SOUTH
            nr = cr + 1
        elif heading == 3:  # WEST
            nc = cc - 1
        # Update wall
        self.grid_map.set_wall_present_between(cr, cc, nr, nc)
        # Blocked cell inference (CMP--3.Execution 2)
        if self.grid_map.in_bounds(nr, nc):
            if self.grid_map.get_cell_state(nr, nc) == CELL_UNKNOWN:
                self.grid_map.set_cell_blocked(nr, nc)

        