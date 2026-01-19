"""
Tic-Tac-Toe Game for LED Matrix Display

Classic tic-tac-toe - two player game with cursor selection.
"""

import numpy as np
import time
from typing import Optional, Tuple, List
from ..game_controller import GameState


class TicTacToeGame(GameState):
    """Tic-Tac-Toe game implementation"""

    def __init__(self, width: int, height: int):
        super().__init__(width, height)

        # Game state
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]  # 0=empty, 1=X, 2=O
        self.current_player = 1  # 1=X, 2=O
        self.winner = None  # None, 1, 2, or 'tie'
        self.cursor_pos = [1, 1]  # [col, row] 0-2
        self.blink_time = 0
        self.show_cursor = True

        # Calculate cell size based on display
        self.cell_size = min(width // 3, height // 3)
        self.grid_offset_x = (width - self.cell_size * 3) // 2
        self.grid_offset_y = (height - self.cell_size * 3) // 2

        self.running = True
        self.game_over = False

    def _check_winner(self) -> Optional[int | str]:
        """
        Check if there's a winner

        Returns:
            1 if player 1 (X) wins
            2 if player 2 (O) wins
            'tie' if board is full
            None if game continues
        """
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != 0:
                return row[0]

        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != 0:
                return self.board[0][col]

        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.board[0][2]

        # Check for tie (board full)
        if all(self.board[row][col] != 0 for row in range(3) for col in range(3)):
            return 'tie'

        return None

    def update(self, dt: float) -> None:
        """Update game logic"""
        # Update cursor blink
        self.blink_time += dt
        if self.blink_time >= 0.5:
            self.show_cursor = not self.show_cursor
            self.blink_time = 0

    def render(self) -> np.ndarray:
        """Render current game state"""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Draw grid lines
        grid_color = [100, 100, 100]

        # Vertical lines
        for i in range(1, 3):
            x = self.grid_offset_x + i * self.cell_size
            for y in range(self.grid_offset_y, self.grid_offset_y + self.cell_size * 3):
                if 0 <= x < self.width and 0 <= y < self.height:
                    frame[y, x] = grid_color

        # Horizontal lines
        for i in range(1, 3):
            y = self.grid_offset_y + i * self.cell_size
            for x in range(self.grid_offset_x, self.grid_offset_x + self.cell_size * 3):
                if 0 <= x < self.width and 0 <= y < self.height:
                    frame[y, x] = grid_color

        # Draw X's and O's
        for row in range(3):
            for col in range(3):
                if self.board[row][col] != 0:
                    self._draw_mark(frame, col, row, self.board[row][col])

        # Draw cursor (if not game over)
        if not self.game_over and self.show_cursor:
            self._draw_cursor(frame, self.cursor_pos[0], self.cursor_pos[1])

        # If game over, flash winner
        if self.game_over and self.winner is not None:
            if self.show_cursor:  # Use blink timer for flash
                if self.winner == 1:
                    # X won - red flash
                    frame[:, :] = [80, 0, 0]
                elif self.winner == 2:
                    # O won - blue flash
                    frame[:, :] = [0, 0, 80]
                else:  # tie
                    # Yellow flash
                    frame[:, :] = [80, 80, 0]

        return frame

    def _draw_mark(self, frame: np.ndarray, col: int, row: int, player: int) -> None:
        """Draw X or O in the specified cell"""
        cell_x = self.grid_offset_x + col * self.cell_size
        cell_y = self.grid_offset_y + row * self.cell_size

        if player == 1:
            # Draw X (red diagonal lines)
            color = [255, 0, 0]
            # Diagonal from top-left to bottom-right
            for i in range(self.cell_size - 2):
                x = cell_x + 1 + i
                y = cell_y + 1 + i
                if 0 <= x < self.width and 0 <= y < self.height:
                    frame[y, x] = color

            # Diagonal from top-right to bottom-left
            for i in range(self.cell_size - 2):
                x = cell_x + self.cell_size - 2 - i
                y = cell_y + 1 + i
                if 0 <= x < self.width and 0 <= y < self.height:
                    frame[y, x] = color

        else:  # player == 2
            # Draw O (blue circle/square outline)
            color = [0, 0, 255]
            center_x = cell_x + self.cell_size // 2
            center_y = cell_y + self.cell_size // 2
            radius = self.cell_size // 3

            # Draw circle outline (or square for small displays)
            for angle in range(0, 360, 20):
                import math
                rad = math.radians(angle)
                x = int(center_x + radius * math.cos(rad))
                y = int(center_y + radius * math.sin(rad))
                if 0 <= x < self.width and 0 <= y < self.height:
                    frame[y, x] = color

    def _draw_cursor(self, frame: np.ndarray, col: int, row: int) -> None:
        """Draw cursor highlight around cell"""
        cell_x = self.grid_offset_x + col * self.cell_size
        cell_y = self.grid_offset_y + row * self.cell_size

        cursor_color = [0, 255, 0]

        # Draw border around cell
        # Top edge
        for x in range(cell_x, cell_x + self.cell_size):
            if 0 <= x < self.width and 0 <= cell_y < self.height:
                frame[cell_y, x] = cursor_color

        # Bottom edge
        y = cell_y + self.cell_size - 1
        for x in range(cell_x, cell_x + self.cell_size):
            if 0 <= x < self.width and 0 <= y < self.height:
                frame[y, x] = cursor_color

        # Left edge
        for y in range(cell_y, cell_y + self.cell_size):
            if 0 <= cell_x < self.width and 0 <= y < self.height:
                frame[y, cell_x] = cursor_color

        # Right edge
        x = cell_x + self.cell_size - 1
        for y in range(cell_y, cell_y + self.cell_size):
            if 0 <= x < self.width and 0 <= y < self.height:
                frame[y, x] = cursor_color

    def handle_input(self, action: str) -> None:
        """Handle player input"""
        if self.game_over:
            if action == 'action' or action == 'reset':
                self.reset()
            return

        # Move cursor
        if action == 'up':
            self.cursor_pos[1] = (self.cursor_pos[1] - 1) % 3
        elif action == 'down':
            self.cursor_pos[1] = (self.cursor_pos[1] + 1) % 3
        elif action == 'left':
            self.cursor_pos[0] = (self.cursor_pos[0] - 1) % 3
        elif action == 'right':
            self.cursor_pos[0] = (self.cursor_pos[0] + 1) % 3

        # Place mark
        elif action == 'action':
            col, row = self.cursor_pos
            if self.board[row][col] == 0:
                # Place mark
                self.board[row][col] = self.current_player

                # Check for winner
                self.winner = self._check_winner()
                if self.winner is not None:
                    self.game_over = True
                    self.running = False
                else:
                    # Switch player
                    self.current_player = 2 if self.current_player == 1 else 1

    def get_state(self) -> dict:
        """Get current game state"""
        state = super().get_state()
        state.update({
            'current_player': 'X' if self.current_player == 1 else 'O',
            'winner': ('X' if self.winner == 1 else 'O') if self.winner in [1, 2] else str(self.winner),
            'moves_made': sum(1 for row in self.board for cell in row if cell != 0)
        })
        return state

    def reset(self) -> None:
        """Reset game to initial state"""
        super().reset()
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        self.current_player = 1
        self.winner = None
        self.cursor_pos = [1, 1]
        self.running = True
        self.game_over = False
