"""
Pong Game for LED Matrix Display

Classic pong game - player vs AI, or auto-play mode.
"""

import numpy as np
import random
from typing import List
from ..game_controller import GameState


class PongGame(GameState):
    """Pong game implementation"""

    def __init__(self, width: int, height: int):
        super().__init__(width, height)

        # Game state
        self.ball_pos = [float(width // 2), float(height // 2)]
        self.ball_vel = self._random_ball_velocity()
        self.paddle_y = float(height // 2)
        self.paddle_height = 6
        self.paddle_width = 1
        self.ai_paddle_y = float(height // 2)
        self.score_player = 0
        self.score_ai = 0
        self.max_score = 9  # Win at 9 points
        self.auto_play = False  # If true, both paddles are AI controlled

        # Paddle speed
        self.paddle_speed = 25.0  # Pixels per second

        # AI tracking speed
        self.ai_speed = 20.0

        self.running = True
        self.game_over = False

    def _random_ball_velocity(self) -> List[float]:
        """Generate random ball velocity"""
        # Random direction (left or right)
        vx = random.choice([-15.0, 15.0])
        # Random vertical component
        vy = random.uniform(-10.0, 10.0)
        return [vx, vy]

    def _reset_ball(self) -> None:
        """Reset ball to center with random velocity"""
        self.ball_pos = [float(self.width // 2), float(self.height // 2)]
        self.ball_vel = self._random_ball_velocity()

    def update(self, dt: float) -> None:
        """Update game logic"""
        if self.game_over:
            return

        # Update ball position
        self.ball_pos[0] += self.ball_vel[0] * dt
        self.ball_pos[1] += self.ball_vel[1] * dt

        # Check top/bottom wall collisions
        if self.ball_pos[1] <= 0:
            self.ball_pos[1] = 0
            self.ball_vel[1] = abs(self.ball_vel[1])
        elif self.ball_pos[1] >= self.height - 1:
            self.ball_pos[1] = self.height - 1
            self.ball_vel[1] = -abs(self.ball_vel[1])

        # Check paddle collisions
        # Left paddle (player)
        if self.ball_pos[0] <= 1 and self.ball_vel[0] < 0:
            paddle_top = self.paddle_y - self.paddle_height // 2
            paddle_bottom = self.paddle_y + self.paddle_height // 2

            if paddle_top <= self.ball_pos[1] <= paddle_bottom:
                # Hit paddle - bounce
                self.ball_pos[0] = 1
                self.ball_vel[0] = abs(self.ball_vel[0])

                # Add angle based on where ball hit paddle
                hit_pos = (self.ball_pos[1] - self.paddle_y) / (self.paddle_height / 2)
                self.ball_vel[1] += hit_pos * 8.0

        # Right paddle (AI)
        if self.ball_pos[0] >= self.width - 2 and self.ball_vel[0] > 0:
            paddle_top = self.ai_paddle_y - self.paddle_height // 2
            paddle_bottom = self.ai_paddle_y + self.paddle_height // 2

            if paddle_top <= self.ball_pos[1] <= paddle_bottom:
                # Hit paddle - bounce
                self.ball_pos[0] = self.width - 2
                self.ball_vel[0] = -abs(self.ball_vel[0])

                # Add angle based on where ball hit paddle
                hit_pos = (self.ball_pos[1] - self.ai_paddle_y) / (self.paddle_height / 2)
                self.ball_vel[1] += hit_pos * 8.0

        # Check goals
        if self.ball_pos[0] < 0:
            # AI scored
            self.score_ai += 1
            self._reset_ball()
            if self.score_ai >= self.max_score:
                self.game_over = True
                self.running = False

        elif self.ball_pos[0] >= self.width:
            # Player scored
            self.score_player += 1
            self._reset_ball()
            if self.score_player >= self.max_score:
                self.game_over = True
                self.running = False

        # AI paddle tracking (simple - follow ball Y)
        if self.ball_pos[1] < self.ai_paddle_y - 1:
            self.ai_paddle_y -= self.ai_speed * dt
        elif self.ball_pos[1] > self.ai_paddle_y + 1:
            self.ai_paddle_y += self.ai_speed * dt

        # Clamp AI paddle to screen
        self.ai_paddle_y = max(self.paddle_height // 2,
                               min(self.height - self.paddle_height // 2, self.ai_paddle_y))

        # Clamp player paddle to screen
        self.paddle_y = max(self.paddle_height // 2,
                           min(self.height - self.paddle_height // 2, self.paddle_y))

    def render(self) -> np.ndarray:
        """Render current game state"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Draw center line (dashed)
        center_x = self.width // 2
        for y in range(0, self.height, 3):
            if y < self.height:
                frame[y, center_x] = [100, 100, 100]

        # Draw left paddle (player)
        paddle_top = int(self.paddle_y - self.paddle_height // 2)
        paddle_bottom = int(self.paddle_y + self.paddle_height // 2)
        for y in range(max(0, paddle_top), min(self.height, paddle_bottom + 1)):
            frame[y, 0] = [255, 255, 255]

        # Draw right paddle (AI)
        ai_paddle_top = int(self.ai_paddle_y - self.paddle_height // 2)
        ai_paddle_bottom = int(self.ai_paddle_y + self.paddle_height // 2)
        for y in range(max(0, ai_paddle_top), min(self.height, ai_paddle_bottom + 1)):
            frame[y, self.width - 1] = [255, 255, 255]

        # Draw ball
        ball_x = int(self.ball_pos[0])
        ball_y = int(self.ball_pos[1])
        if 0 <= ball_x < self.width and 0 <= ball_y < self.height:
            frame[ball_y, ball_x] = [255, 255, 255]

        # Draw score (simple pixel representation at top)
        # Player score on left
        for i in range(min(self.score_player, 9)):
            if i < self.width // 2 - 2:
                frame[0, i + 1] = [0, 255, 0]

        # AI score on right
        for i in range(min(self.score_ai, 9)):
            if self.width - 2 - i >= self.width // 2 + 2:
                frame[0, self.width - 2 - i] = [255, 0, 0]

        # If game over, flash the screen
        if self.game_over:
            if int(self.ball_pos[0] * 4) % 2 == 0:
                if self.score_player >= self.max_score:
                    frame[:, :] = [0, 100, 0]  # Green flash (player won)
                else:
                    frame[:, :] = [100, 0, 0]  # Red flash (AI won)

        return frame

    def handle_input(self, action: str) -> None:
        """Handle player input"""
        if action == 'up':
            self.paddle_y -= 2
        elif action == 'down':
            self.paddle_y += 2
        elif action == 'action' and self.game_over:
            self.reset()
        elif action == 'left':
            # Toggle auto-play mode
            self.auto_play = not self.auto_play
        elif action == 'right':
            # Toggle auto-play mode
            self.auto_play = not self.auto_play

        # In auto-play mode, left paddle also tracks ball
        if self.auto_play:
            if self.ball_pos[1] < self.paddle_y - 1:
                self.paddle_y -= 1
            elif self.ball_pos[1] > self.paddle_y + 1:
                self.paddle_y += 1

    def get_state(self) -> dict:
        """Get current game state"""
        state = super().get_state()
        state.update({
            'score': self.score_player,
            'ai_score': self.score_ai,
            'auto_play': self.auto_play
        })
        return state

    def reset(self) -> None:
        """Reset game to initial state"""
        super().reset()
        self.ball_pos = [float(self.width // 2), float(self.height // 2)]
        self.ball_vel = self._random_ball_velocity()
        self.paddle_y = float(self.height // 2)
        self.ai_paddle_y = float(self.height // 2)
        self.score_player = 0
        self.score_ai = 0
        self.running = True
        self.game_over = False
