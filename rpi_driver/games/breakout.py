"""
Breakout/Arkanoid Game for LED Matrix Display

Classic brick-breaking game with paddle and ball.
"""

import numpy as np
import random
from typing import List, Tuple
from ..game_controller import GameState


class BreakoutGame(GameState):
    """Breakout game implementation"""

    def __init__(self, width: int, height: int):
        super().__init__(width, height)

        # Game state
        self.ball_pos = [float(width // 2), float(height - 5)]
        self.ball_vel = [0.0, 0.0]
        self.ball_stuck = True  # Ball attached to paddle initially
        self.paddle_x = float(width // 2)
        self.paddle_width = 6
        self.paddle_speed = 30.0  # Pixels per second
        self.ball_speed = 20.0  # Base ball speed

        # Bricks
        self.bricks = self._create_brick_grid()
        self.brick_rows = 5
        self.brick_cols = width
        self.brick_height = 2

        # Score and lives
        self.score = 0
        self.lives = 3
        self.level = 1

        self.running = True
        self.game_over = False

    def _create_brick_grid(self) -> np.ndarray:
        """Create brick grid (1 = brick exists, 0 = destroyed)"""
        # Create 5 rows of bricks at the top
        bricks = np.ones((5, self.width), dtype=bool)
        return bricks

    def _launch_ball(self) -> None:
        """Launch ball from paddle"""
        if self.ball_stuck:
            # Launch at random angle upward
            angle = random.uniform(-0.6, 0.6)  # Angle from vertical
            self.ball_vel = [
                self.ball_speed * angle,
                -self.ball_speed
            ]
            self.ball_stuck = False

    def update(self, dt: float) -> None:
        """Update game logic"""
        if self.game_over:
            return

        # Update ball if not stuck
        if not self.ball_stuck:
            self.ball_pos[0] += self.ball_vel[0] * dt
            self.ball_pos[1] += self.ball_vel[1] * dt

            # Check wall collisions (left/right)
            if self.ball_pos[0] <= 0:
                self.ball_pos[0] = 0
                self.ball_vel[0] = abs(self.ball_vel[0])
            elif self.ball_pos[0] >= self.width - 1:
                self.ball_pos[0] = self.width - 1
                self.ball_vel[0] = -abs(self.ball_vel[0])

            # Check top wall collision
            if self.ball_pos[1] <= 0:
                self.ball_pos[1] = 0
                self.ball_vel[1] = abs(self.ball_vel[1])

            # Check paddle collision
            paddle_y = self.height - 2
            if (paddle_y <= self.ball_pos[1] <= paddle_y + 1 and
                self.ball_vel[1] > 0):
                paddle_left = self.paddle_x - self.paddle_width // 2
                paddle_right = self.paddle_x + self.paddle_width // 2

                if paddle_left <= self.ball_pos[0] <= paddle_right:
                    # Hit paddle
                    self.ball_pos[1] = paddle_y
                    self.ball_vel[1] = -abs(self.ball_vel[1])

                    # Add horizontal velocity based on where ball hit paddle
                    hit_offset = (self.ball_pos[0] - self.paddle_x) / (self.paddle_width / 2)
                    self.ball_vel[0] += hit_offset * 5.0

            # Check brick collisions
            ball_x = int(self.ball_pos[0])
            ball_y = int(self.ball_pos[1])

            if 0 <= ball_y < self.brick_rows and 0 <= ball_x < self.width:
                if self.bricks[ball_y, ball_x]:
                    # Hit brick
                    self.bricks[ball_y, ball_x] = False
                    self.ball_vel[1] = -self.ball_vel[1]
                    self.score += 10

                    # Check if all bricks destroyed (level complete)
                    if not np.any(self.bricks):
                        self._next_level()

            # Check death (ball fell below paddle)
            if self.ball_pos[1] >= self.height:
                self._lose_life()

        else:
            # Ball stuck to paddle - update position
            self.ball_pos[0] = self.paddle_x
            self.ball_pos[1] = self.height - 3

    def _lose_life(self) -> None:
        """Lose a life"""
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
            self.running = False
        else:
            # Reset ball
            self.ball_stuck = True
            self.ball_pos = [self.paddle_x, float(self.height - 3)]
            self.ball_vel = [0.0, 0.0]

    def _next_level(self) -> None:
        """Advance to next level"""
        self.level += 1
        self.ball_stuck = True
        self.ball_pos = [self.paddle_x, float(self.height - 3)]
        self.ball_vel = [0.0, 0.0]
        self.bricks = self._create_brick_grid()
        self.ball_speed += 2.0  # Increase ball speed each level

    def render(self) -> np.ndarray:
        """Render current game state"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Draw bricks (rainbow colors by row)
        brick_colors = [
            [255, 0, 0],    # Red
            [255, 128, 0],  # Orange
            [255, 255, 0],  # Yellow
            [0, 255, 0],    # Green
            [0, 128, 255],  # Blue
        ]

        for row in range(self.brick_rows):
            for col in range(self.width):
                if self.bricks[row, col]:
                    frame[row, col] = brick_colors[row % len(brick_colors)]

        # Draw paddle (white)
        paddle_y = self.height - 2
        paddle_left = int(self.paddle_x - self.paddle_width // 2)
        paddle_right = int(self.paddle_x + self.paddle_width // 2)

        for x in range(max(0, paddle_left), min(self.width, paddle_right + 1)):
            frame[paddle_y, x] = [255, 255, 255]

        # Draw ball (white)
        ball_x = int(self.ball_pos[0])
        ball_y = int(self.ball_pos[1])
        if 0 <= ball_x < self.width and 0 <= ball_y < self.height:
            frame[ball_y, ball_x] = [255, 255, 255]

        # Draw lives indicator (small dots at bottom-right)
        for i in range(self.lives):
            if self.width - 1 - i >= 0:
                frame[self.height - 1, self.width - 1 - i] = [0, 255, 0]

        # If game over, flash screen
        if self.game_over:
            if int(self.ball_pos[0] * 4) % 2 == 0:
                frame[:, :] = [100, 0, 0]  # Red flash

        return frame

    def handle_input(self, action: str) -> None:
        """Handle player input"""
        if action == 'left':
            self.paddle_x -= 2
        elif action == 'right':
            self.paddle_x += 2
        elif action == 'action':
            if self.game_over:
                self.reset()
            else:
                self._launch_ball()

        # Clamp paddle to screen
        self.paddle_x = max(self.paddle_width // 2,
                           min(self.width - self.paddle_width // 2, self.paddle_x))

    def get_state(self) -> dict:
        """Get current game state"""
        state = super().get_state()
        state.update({
            'score': self.score,
            'lives': self.lives,
            'level': self.level,
            'bricks_remaining': int(np.sum(self.bricks))
        })
        return state

    def reset(self) -> None:
        """Reset game to initial state"""
        super().reset()
        self.ball_pos = [float(self.width // 2), float(self.height - 5)]
        self.ball_vel = [0.0, 0.0]
        self.ball_stuck = True
        self.paddle_x = float(self.width // 2)
        self.bricks = self._create_brick_grid()
        self.score = 0
        self.lives = 3
        self.level = 1
        self.ball_speed = 20.0
        self.running = True
        self.game_over = False
