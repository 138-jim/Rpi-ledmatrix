"""
BLE Protocol definitions for LED Matrix Controller

This module defines the Bluetooth Low Energy protocol used to communicate
between the iPhone app and the Raspberry Pi LED display.
"""

# BLE Service and Characteristic UUIDs
# Custom UUIDs generated for LED Matrix control
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"

CHAR_BRIGHTNESS_UUID = "12345678-1234-5678-1234-56789abcdef1"
CHAR_PATTERN_UUID = "12345678-1234-5678-1234-56789abcdef2"
CHAR_GAME_CONTROL_UUID = "12345678-1234-5678-1234-56789abcdef3"
CHAR_STATUS_UUID = "12345678-1234-5678-1234-56789abcdef4"
CHAR_CONFIG_UUID = "12345678-1234-5678-1234-56789abcdef5"
CHAR_POWER_LIMIT_UUID = "12345678-1234-5678-1234-56789abcdef6"
CHAR_SLEEP_SCHEDULE_UUID = "12345678-1234-5678-1234-56789abcdef7"
CHAR_FRAME_STREAM_UUID = "12345678-1234-5678-1234-56789abcdef8"
CHAR_PATTERN_LIST_UUID = "12345678-1234-5678-1234-56789abcdef9"

# Pattern indices (0-36 for 37 patterns)
PATTERNS = [
    # Solid Colors (0-3)
    "red", "green", "blue", "white",

    # Geometric (4-8)
    "corners", "cross", "checkerboard", "grid", "panels",

    # Animated Effects (9-13)
    "spiral", "wave", "fire", "plasma", "geometric_patterns",

    # Gradients & Colors (14-17)
    "rainbow", "color_gradients", "gradient_waves", "rgb_torch",

    # Natural Phenomena (18-26)
    "snow", "rain", "fireflies", "aquarium", "ocean_waves",
    "northern_lights", "starfield", "starry_night", "fireworks",

    # Complex Animations (27-32)
    "heart", "dna_helix", "kaleidoscope", "perlin_noise_flow",
    "matrix_rain", "lava_lamp",

    # Time-based (33-36)
    "elapsed", "sunset_sunrise", "sunset_sunrise_loop", "dot"
]

# Game indices (0-4)
GAMES = [
    "snake",
    "pong",
    "tictactoe",
    "breakout",
    "tetris"
]

# Game actions (0-7)
ACTIONS = [
    "up",
    "down",
    "left",
    "right",
    "action",
    "reset",
    "pause",
    "resume"
]

def get_pattern_name(index: int) -> str:
    """Get pattern name from index"""
    if 0 <= index < len(PATTERNS):
        return PATTERNS[index]
    return None

def get_pattern_index(name: str) -> int:
    """Get pattern index from name"""
    try:
        return PATTERNS.index(name)
    except ValueError:
        return -1

def get_game_name(index: int) -> str:
    """Get game name from index"""
    if 0 <= index < len(GAMES):
        return GAMES[index]
    return None

def get_action_name(index: int) -> str:
    """Get action name from index"""
    if 0 <= index < len(ACTIONS):
        return ACTIONS[index]
    return None

def get_pattern_list_json() -> str:
    """Get pattern list as JSON string"""
    import json
    return json.dumps({
        "patterns": PATTERNS,
        "count": len(PATTERNS)
    })

def get_game_list_json() -> str:
    """Get game list as JSON string"""
    import json
    return json.dumps({
        "games": GAMES,
        "count": len(GAMES)
    })

# Frame streaming constants
MAX_CHUNK_SIZE = 500  # Maximum bytes per BLE write
FRAME_TIMEOUT = 1.0   # Seconds before incomplete frame is discarded
