"""
Tetris Game for LED Matrix Display

Classic Tetris with 7 tetromino shapes, rotation, and line clearing.
"""

import numpy as np
import random
from typing import List, Tuple
from ..game_controller import GameState


# Tetromino shapes (4x4 grids for all rotations)
TETROMINOES = {
    'I': [
        [[0, 0, 0, 0],
         [1, 1, 1, 1],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0]]
    ],
    'O': [
        [[0, 1, 1, 0],
         [0, 1, 1, 0],
         [0, 0, 0, 0],
         [0, 0, 0, 0]]
    ],
    'T': [
        [[0, 1, 0, 0],
         [1, 1, 1, 0],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [0, 1, 1, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]],
        [[0, 0, 0, 0],
         [1, 1, 1, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [1, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]]
    ],
    'S': [
        [[0, 1, 1, 0],
         [1, 1, 0, 0],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [0, 1, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 0, 0]]
    ],
    'Z': [
        [[1, 1, 0, 0],
         [0, 1, 1, 0],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 0, 1, 0],
         [0, 1, 1, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]]
    ],
    'J': [
        [[1, 0, 0, 0],
         [1, 1, 1, 0],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 1, 1, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]],
        [[0, 0, 0, 0],
         [1, 1, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [0, 1, 0, 0],
         [1, 1, 0, 0],
         [0, 0, 0, 0]]
    ],
    'L': [
        [[0, 0, 1, 0],
         [1, 1, 1, 0],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 1, 0],
         [0, 0, 0, 0]],
        [[0, 0, 0, 0],
         [1, 1, 1, 0],
         [1, 0, 0, 0],
         [0, 0, 0, 0]],
        [[1, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 0]]
    ]
}

# Colors for each piece type
TETROMINO_COLORS = {
    'I': [0, 255, 255],    # Cyan
    'O': [255, 255, 0],    # Yellow
    'T': [128, 0, 128],    # Purple
    'S': [0, 255, 0],      # Green
    'Z': [255, 0, 0],      # Red
    'J': [0, 0, 255],      # Blue
    'L': [255, 128, 0]     # Orange
}


class TetrisGame(GameState):
    """Tetris game implementation"""

    def __init__(self, width: int, height: int):
        super().__init__(width, height)

        # Adjust grid dimensions for Tetris (typically 10 wide, 20 tall)
        self.grid_width = min(10, width)
        self.grid_height = min(20, height)
        self.grid_offset_x = (width - self.grid_width) // 2

        # Game state
        self.grid = np.zeros((self.grid_height, self.grid_width), dtype=int)
        self.current_piece = None
        self.current_piece_type = None
        self.piece_x = 0
        self.piece_y = 0
        self.piece_rotation = 0
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_timer = 0
        self.fall_speed = 1.0  # Seconds per fall
        self.fast_fall = False

        self._spawn_piece()

        self.running = True
        self.game_over = False

    def _spawn_piece(self) -> None:
        """Spawn a new random piece at the top"""
        piece_types = list(TETROMINOES.keys())
        self.current_piece_type = random.choice(piece_types)
        self.current_piece = TETROMINOES[self.current_piece_type][0]
        self.piece_rotation = 0
        self.piece_x = self.grid_width // 2 - 2
        self.piece_y = 0

        # Check if piece can spawn (game over if not)
        if self._check_collision(self.piece_x, self.piece_y, self.current_piece):
            self.game_over = True
            self.running = False

    def _get_current_rotations(self) -> List:
        """Get rotation states for current piece"""
        return TETROMINOES[self.current_piece_type]

    def _check_collision(self, x: int, y: int, piece: List) -> bool:
        """Check if piece collides with grid or boundaries"""
        for row in range(4):
            for col in range(4):
                if piece[row][col]:
                    grid_x = x + col
                    grid_y = y + row

                    # Check boundaries
                    if grid_x < 0 or grid_x >= self.grid_width:
                        return True
                    if grid_y < 0 or grid_y >= self.grid_height:
                        return True

                    # Check grid collision
                    if self.grid[grid_y, grid_x]:
                        return True

        return False

    def _lock_piece(self) -> None:
        """Lock current piece into grid"""
        for row in range(4):
            for col in range(4):
                if self.current_piece[row][col]:
                    grid_x = self.piece_x + col
                    grid_y = self.piece_y + row
                    if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
                        # Store piece type as grid value (1-7)
                        piece_types = list(TETROMINOES.keys())
                        piece_id = piece_types.index(self.current_piece_type) + 1
                        self.grid[grid_y, grid_x] = piece_id

        # Check for completed lines
        self._clear_lines()

        # Spawn new piece
        self._spawn_piece()

    def _clear_lines(self) -> None:
        """Clear completed lines and update score"""
        lines_to_clear = []

        for y in range(self.grid_height):
            if np.all(self.grid[y, :]):
                lines_to_clear.append(y)

        if lines_to_clear:
            # Remove cleared lines
            for y in sorted(lines_to_clear, reverse=True):
                self.grid = np.delete(self.grid, y, axis=0)
                # Add empty line at top
                self.grid = np.vstack([np.zeros((1, self.grid_width), dtype=int), self.grid])

            # Update score (Tetris scoring)
            lines_count = len(lines_to_clear)
            points = [0, 40, 100, 300, 1200]  # 1, 2, 3, 4 lines
            self.score += points[lines_count] * self.level
            self.lines_cleared += lines_count

            # Level up every 10 lines
            new_level = (self.lines_cleared // 10) + 1
            if new_level > self.level:
                self.level = new_level
                self.fall_speed = max(0.1, 1.0 - (self.level - 1) * 0.1)

    def update(self, dt: float) -> None:
        """Update game logic"""
        if self.game_over:
            return

        # Update fall timer
        current_fall_speed = self.fall_speed if not self.fast_fall else self.fall_speed / 10
        self.fall_timer += dt

        if self.fall_timer >= current_fall_speed:
            self.fall_timer = 0

            # Move piece down
            if not self._check_collision(self.piece_x, self.piece_y + 1, self.current_piece):
                self.piece_y += 1
            else:
                # Lock piece and spawn new one
                self._lock_piece()

    def render(self) -> np.ndarray:
        """Render current game state"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Draw grid contents
        piece_types = list(TETROMINOES.keys())
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.grid[y, x]:
                    piece_type = piece_types[self.grid[y, x] - 1]
                    color = TETROMINO_COLORS[piece_type]
                    screen_x = self.grid_offset_x + x
                    if 0 <= screen_x < self.width and 0 <= y < self.height:
                        frame[y, screen_x] = color

        # Draw current piece
        if self.current_piece:
            color = TETROMINO_COLORS[self.current_piece_type]
            for row in range(4):
                for col in range(4):
                    if self.current_piece[row][col]:
                        screen_x = self.grid_offset_x + self.piece_x + col
                        screen_y = self.piece_y + row
                        if (0 <= screen_x < self.width and
                            0 <= screen_y < self.height):
                            frame[screen_y, screen_x] = color

        # Draw grid borders (if space available)
        border_color = [100, 100, 100]
        if self.grid_offset_x > 0:
            # Left border
            for y in range(min(self.grid_height, self.height)):
                frame[y, self.grid_offset_x - 1] = border_color

        if self.grid_offset_x + self.grid_width < self.width:
            # Right border
            for y in range(min(self.grid_height, self.height)):
                frame[y, self.grid_offset_x + self.grid_width] = border_color

        # Game over flash
        if self.game_over:
            if int(self.fall_timer * 4) % 2 == 0:
                frame[:, :] = [100, 0, 0]

        return frame

    def handle_input(self, action: str) -> None:
        """Handle player input"""
        if self.game_over:
            if action == 'action' or action == 'reset':
                self.reset()
            return

        if action == 'left':
            # Move left
            if not self._check_collision(self.piece_x - 1, self.piece_y, self.current_piece):
                self.piece_x -= 1

        elif action == 'right':
            # Move right
            if not self._check_collision(self.piece_x + 1, self.piece_y, self.current_piece):
                self.piece_x += 1

        elif action == 'down':
            # Soft drop (faster fall)
            self.fast_fall = True

        elif action == 'up' or action == 'action':
            # Rotate clockwise
            rotations = self._get_current_rotations()
            new_rotation = (self.piece_rotation + 1) % len(rotations)
            new_piece = rotations[new_rotation]

            # Check if rotation is valid
            if not self._check_collision(self.piece_x, self.piece_y, new_piece):
                self.current_piece = new_piece
                self.piece_rotation = new_rotation
            # Try wall kick (move left/right to make rotation fit)
            elif not self._check_collision(self.piece_x - 1, self.piece_y, new_piece):
                self.piece_x -= 1
                self.current_piece = new_piece
                self.piece_rotation = new_rotation
            elif not self._check_collision(self.piece_x + 1, self.piece_y, new_piece):
                self.piece_x += 1
                self.current_piece = new_piece
                self.piece_rotation = new_rotation

    def get_state(self) -> dict:
        """Get current game state"""
        state = super().get_state()
        state.update({
            'score': self.score,
            'level': self.level,
            'lines': self.lines_cleared
        })
        return state

    def reset(self) -> None:
        """Reset game to initial state"""
        super().reset()
        self.grid = np.zeros((self.grid_height, self.grid_width), dtype=int)
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_timer = 0
        self.fall_speed = 1.0
        self.fast_fall = False
        self._spawn_piece()
        self.running = True
        self.game_over = False
