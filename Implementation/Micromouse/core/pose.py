

"""
Pose Estimation Module.

Traces:
- CMP--9 Pose Estimation Module
"""

import time


class PoseEstimator:
    def __init__(self, config):
        self.config = config
        # Continuous pose
        self.x_cm = 0.0
        self.y_cm = 0.0
        self.theta_deg = 0.0  # 0: +y (NORTH) for simplicity
        # Discrete pose
        self.cell = (0, 0)
        self.heading = 0  # 0:N,1:E,2:S,3:W

    def update(self, motion):
        """
        Simplified update: we don't integrate real kinematics but,
        for demonstration, we keep fixed cell/heading.
        In a full implementation, integrate wheel speeds over T. (CMP--9.Execution)
        """
        # Map continuous pose to cell indices
        r, c = self.cell
        if r < 0:
            r = 0
        if r >= self.config.rows:
            r = self.config.rows - 1
        if c < 0:
            c = 0
        if c >= self.config.cols:
            c = self.config.cols - 1
        self.cell = (r, c)
        # Heading stays discretized
        self.heading = self.heading % 4

    def get_pose_estimate(self):
        """Return PoseEstimate for mission control etc. (CMP--9.ConnectedComponents)"""
        return {
            "cell": self.cell,
            "heading": self.heading,
        }

        