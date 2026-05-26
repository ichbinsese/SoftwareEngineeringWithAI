
# Shared enums and constants.
# Trace:
#   - DAT--1 GridMap.Direction
#   - DAT--4 Direction enum
#   - Used by CMP--2, CMP--3, CMP--4, CMP--5, CMP--6, CMP--9

class Direction:
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


def direction_to_dx_dy(direction):
    # DAT--4: neighbor directions on 4x8 grid (x in [0..3], y in [0..7])
    if direction == Direction.NORTH:
        return 0, 1
    if direction == Direction.EAST:
        return 1, 0
    if direction == Direction.SOUTH:
        return 0, -1
    if direction == Direction.WEST:
        return -1, 0
    return 0, 0


def opposite_direction(direction):
    return (direction + 2) % 4
