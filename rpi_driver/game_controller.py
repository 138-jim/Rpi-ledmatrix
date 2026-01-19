"""
Game Controller for LED Matrix Display

Manages interactive games with state persistence, input handling, and frame generation.
"""

import numpy as np
import threading
import time
import queue
from typing import Optional, Dict, Callable
from abc import ABC, abstractmethod


class GameState(ABC):
    """Base class for game state management"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.running = False
        self.game_over = False
        self.paused = False

    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update game logic (called every frame)

        Args:
            dt: Delta time in seconds since last update
        """
        pass

    @abstractmethod
    def render(self) -> np.ndarray:
        """
        Render current state to frame

        Returns:
            np.ndarray: Frame array (height, width, 3) in RGB format
        """
        pass

    @abstractmethod
    def handle_input(self, action: str) -> None:
        """
        Handle player input

        Args:
            action: Input action string (e.g., 'up', 'down', 'left', 'right', 'action')
        """
        pass

    def get_state(self) -> Dict:
        """
        Get current game state for UI display

        Returns:
            Dict containing game state (score, lives, level, etc.)
        """
        return {
            'running': self.running,
            'game_over': self.game_over,
            'paused': self.paused
        }

    def reset(self) -> None:
        """Reset game to initial state"""
        self.game_over = False
        self.paused = False


class GameController:
    """Manages game state and frame generation"""

    def __init__(self, frame_queue: queue.Queue, width: int, height: int):
        """
        Initialize game controller

        Args:
            frame_queue: Queue to put rendered frames into
            width: Display width in pixels
            height: Display height in pixels
        """
        self.frame_queue = frame_queue
        self.width = width
        self.height = height
        self.current_game: Optional[GameState] = None
        self.current_game_name: Optional[str] = None
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.target_fps = 30
        self.actual_fps = 0

    def start_game(self, game_name: str, game_class: Callable) -> bool:
        """
        Start a specific game

        Args:
            game_name: Name of the game
            game_class: GameState subclass to instantiate

        Returns:
            bool: True if game started successfully
        """
        # Stop any running game first
        self.stop()

        try:
            # Create new game instance
            self.current_game = game_class(self.width, self.height)
            self.current_game_name = game_name
            self.current_game.running = True
            self.running = True

            # Start game loop thread
            self.thread = threading.Thread(target=self._game_loop, daemon=True)
            self.thread.start()

            return True
        except Exception as e:
            print(f"Error starting game {game_name}: {e}")
            return False

    def stop(self) -> None:
        """Stop current game"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.current_game = None
        self.current_game_name = None

    def send_input(self, action: str) -> bool:
        """
        Send input to current game

        Args:
            action: Input action string

        Returns:
            bool: True if input was handled
        """
        if self.current_game and self.current_game.running:
            self.current_game.handle_input(action)
            return True
        return False

    def get_state(self) -> Dict:
        """
        Get current game state

        Returns:
            Dict containing game state
        """
        if self.current_game:
            state = self.current_game.get_state()
            state['game_name'] = self.current_game_name
            state['fps'] = self.actual_fps
            return state
        return {
            'running': False,
            'game_name': None,
            'fps': 0
        }

    def pause(self) -> None:
        """Pause current game"""
        if self.current_game:
            self.current_game.paused = True

    def resume(self) -> None:
        """Resume current game"""
        if self.current_game:
            self.current_game.paused = False

    def reset(self) -> None:
        """Reset current game"""
        if self.current_game:
            self.current_game.reset()

    def _game_loop(self) -> None:
        """Main game loop running at target FPS"""
        frame_time = 1.0 / self.target_fps
        last_time = time.time()
        fps_counter = 0
        fps_timer = time.time()

        while self.running and self.current_game:
            loop_start = time.time()

            # Calculate delta time
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time

            # Update game logic (if not paused)
            if not self.current_game.paused:
                self.current_game.update(dt)

            # Render frame
            try:
                frame = self.current_game.render()

                # Put frame in queue (non-blocking to avoid backup)
                try:
                    self.frame_queue.put_nowait(frame)
                except queue.Full:
                    # Queue full, skip this frame
                    pass
            except Exception as e:
                print(f"Error rendering game frame: {e}")

            # FPS calculation
            fps_counter += 1
            if current_time - fps_timer >= 1.0:
                self.actual_fps = fps_counter
                fps_counter = 0
                fps_timer = current_time

            # Sleep to maintain target FPS
            elapsed = time.time() - loop_start
            sleep_time = frame_time - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)


# Game registry - will be populated by importing game modules
GAMES: Dict[str, type] = {}


def register_game(name: str, game_class: type) -> None:
    """
    Register a game class

    Args:
        name: Game name
        game_class: GameState subclass
    """
    GAMES[name] = game_class
