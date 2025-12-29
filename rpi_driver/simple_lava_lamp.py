"""
Simple Lava Lamp Animation
Based on Shadertoy implementation by Jessica Plotkin
https://www.shadertoy.com/view/NdSSzw

Uses simple sin/cos animation instead of physics simulation for performance.
"""

import numpy as np
import time
import math


class SimpleLavaLamp:
    """Simple lava lamp with sin/cos animated metaballs"""

    def __init__(self, width: int = 32, height: int = 32):
        self.width = width
        self.height = height
        self.start_time = time.time()

        # 10 blobs with different animation parameters
        self.blobs = [
            {'x_speed': 0.01, 'x_range': 0.3, 'y_speed': 0.25, 'y_range': 0.4, 'radius': 0.03},
            {'x_speed': 0.02, 'x_range': 0.1, 'y_speed': 0.2, 'y_range': 0.5, 'radius': 0.025},
            {'x_speed': 0.025, 'x_range': 0.3, 'y_speed': 0.1, 'y_range': 0.5, 'radius': 0.035},
            {'x_speed': 0.02, 'x_range': 0.2, 'y_speed': 0.18, 'y_range': 0.5, 'radius': 0.035},
            {'x_speed': 0.03, 'x_range': 0.3, 'y_speed': 0.25, 'y_range': 0.4, 'radius': 0.03},
            {'x_speed': 0.03, 'x_range': 0.1, 'y_speed': 0.15, 'y_range': 0.5, 'radius': 0.035},
            {'x_speed': 0.01, 'x_range': 0.3, 'y_speed': 0.1, 'y_range': 0.5, 'radius': 0.045},
            {'x_speed': 0.02, 'x_range': 0.2, 'y_speed': 0.12, 'y_range': 0.5, 'radius': 0.028},
            {'x_speed': 0.024, 'x_range': 0.3, 'y_speed': 0.22, 'y_range': 0.5, 'radius': 0.032},
            {'x_speed': 0.03, 'x_range': 0.1, 'y_speed': 0.3, 'y_range': 0.5, 'radius': 0.030},
        ]

    def scale_by_temp(self, y_norm: float) -> float:
        """Scale blob size by temperature (height) - hotter = bigger"""
        return 1.0 / math.log(y_norm + 2.0) - 0.6

    def get_blob_position(self, blob_idx: int, t: float) -> tuple:
        """Get blob position at time t using sin/cos animation"""
        blob = self.blobs[blob_idx]

        x = math.sin(t * blob['x_speed']) * blob['x_range']
        y = math.cos(t * blob['y_speed']) * blob['y_range']

        return (x, y)

    def render_frame(self) -> np.ndarray:
        """Render current frame"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Current time
        t = time.time() - self.start_time

        # Normalize coordinates to -0.5 to 0.5
        for py in range(self.height):
            for px in range(self.width):
                # Normalize pixel position to [-0.5, 0.5]
                uv_x = (px / self.width) - 0.5
                uv_y = (py / self.height) - 0.5

                # Aspect ratio correction (assuming square panels)
                # uv_x *= self.width / self.height

                # Metaball field accumulator
                field = 0.0

                # Add contribution from all blobs
                for i in range(len(self.blobs)):
                    blob_x, blob_y = self.get_blob_position(i, t)

                    # Temperature scaling based on Y position
                    temp_scale = self.scale_by_temp(blob_y + 0.5)
                    radius = self.blobs[i]['radius'] * max(0.5, temp_scale * 2.0)

                    # Distance from pixel to blob center
                    dx = uv_x - blob_x
                    dy = uv_y - blob_y
                    dist = math.sqrt(dx * dx + dy * dy)

                    # Metaball contribution: radius / distance
                    if dist > 0.001:  # Avoid division by zero
                        field += radius / dist

                # Threshold and color based on field strength
                if field > 0.5:  # Threshold for blob visibility
                    # Normalize field for color intensity
                    intensity = min(1.0, field / 2.0)

                    # Lava lamp colors - orange/yellow when hot (top), red when cool (bottom)
                    # Y position determines temperature
                    temp = (py / self.height)  # 0 = top (hot), 1 = bottom (cool)

                    if temp < 0.3:  # Hot (top) - bright yellow/orange
                        r = int(255 * intensity)
                        g = int(200 * intensity)
                        b = int(50 * intensity)
                    elif temp < 0.6:  # Warm - orange
                        r = int(255 * intensity)
                        g = int(150 * intensity)
                        b = int(30 * intensity)
                    else:  # Cool (bottom) - red
                        r = int(220 * intensity)
                        g = int(50 * intensity)
                        b = int(20 * intensity)

                    frame[py, px] = [r, g, b]
                else:
                    # Background color - dark purple
                    frame[py, px] = [10, 0, 20]

        return frame
