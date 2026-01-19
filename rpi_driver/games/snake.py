"""
Snake Game for LED Matrix Display

Classic snake game - eat food to grow, avoid hitting yourself or walls.
"""

import numpy as np
import random
from typing import List, Tuple
from ..game_controller import GameState


class SnakeGame(GameState):
    """Snake game implementation"""

    def __init__(self, width: int, height: int):
        super().__init__(width, height)

        # Game state
        self.snake: List[Tuple[int, int]] = [(width // 2, height // 2)]
        self.direction = (1, 0)  # Start moving right
        self.next_direction = (1, 0)  # Buffered direction change
        self.food = self._spawn_food()
        self.score = 0
        self.speed = 5  # Moves per second
        self.move_timer = 0
        self.running = True
        self.game_over = False

    def _spawn_food(self) -> Tuple[int, int]:
        """Spawn food at random empty location"""
        while True:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            if (x, y) not in self.snake:
                return (x, y)

    def update(self, dt: float) -> None:
        """Update game logic"""
        if self.game_over:
            return

        # Update move timer
        self.move_timer += dt
        move_interval = 1.0 / self.speed

        if self.move_timer >= move_interval:
            self.move_timer = 0

            # Update direction (from buffered next_direction)
            self.direction = self.next_direction

            # Calculate new head position
            head_x, head_y = self.snake[0]
            new_head = (
                (head_x + self.direction[0]) % self.width,
                (head_y + self.direction[1]) % self.height
            )

            # Check self collision
            if new_head in self.snake:
                self.game_over = True
                self.running = False
                return

            # Add new head
            self.snake.insert(0, new_head)

            # Check food collision
            if new_head == self.food:
                self.score += 10
                self.food = self._spawn_food()
                # Increase speed slightly
                self.speed = min(15, self.speed + 0.2)
            else:
                # Remove tail (snake doesn't grow)
                self.snake.pop()

    def render(self) -> np.ndarray:
        """Render current game state"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Draw snake body (green)
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                # Head is yellow
                frame[y, x] = [255, 255, 0]
            else:
                # Body is green
                frame[y, x] = [0, 255, 0]

        # Draw food (red)
        if self.food:
            food_x, food_y = self.food
            frame[food_y, food_x] = [255, 0, 0]

        # If game over, flash the screen
        if self.game_over:
            if int(self.move_timer * 4) % 2 == 0:
                frame[:, :] = [100, 0, 0]  # Red flash

        return frame

    def handle_input(self, action: str) -> None:
        """Handle player input"""
        # Map action to direction, but prevent reversing
        direction_map = {
            'up': (0, -1),
            'down': (0, 1),
            'left': (-1, 0),
            'right': (1, 0)
        }

        if action in direction_map:
            new_dir = direction_map[action]
            # Check if new direction is not opposite of current direction
            if (new_dir[0] + self.direction[0] != 0 or
                new_dir[1] + self.direction[1] != 0):
                self.next_direction = new_dir

        # Reset game on action button
        if action == 'action' and self.game_over:
            self.reset()

    def get_state(self) -> dict:
        """Get current game state"""
        state = super().get_state()
        state.update({
            'score': self.score,
            'length': len(self.snake),
            'speed': self.speed
        })
        return state

    def reset(self) -> None:
        """Reset game to initial state"""
        super().reset()
        self.snake = [(self.width // 2, self.height // 2)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = self._spawn_food()
        self.score = 0
        self.speed = 5
        self.move_timer = 0
        self.running = True
        self.game_over = False
