# LED Matrix Controller

A Raspberry Pi controller for ESP32-based LED matrices. The ESP32 acts as a simple frame display device while the Raspberry Pi handles all text rendering, patterns, and animations.

## Architecture

- **ESP32**: Receives RGB frame data via serial and displays it on the LED matrix
- **Raspberry Pi**: Generates text, patterns, animations and sends frames to ESP32

## Setup

### 1. ESP32 Setup
Upload `esp32_frame_display.ino` to your ESP32 using Arduino IDE.

### 2. Raspberry Pi Setup
```bash
./install_dependencies.sh
# Logout and login again for serial permissions
```

### 3. Hardware Connection
Connect ESP32 to Raspberry Pi via USB cable.

## Usage

```bash
python3 led_matrix_controller.py
```

### Commands
- `text:<message>` - Set scrolling text
- `color:<r>,<g>,<b>` - Set text color (0-255)
- `brightness:<0-255>` - Set LED brightness
- `pattern:<name>` - Show pattern (rainbow, spiral, wave)
- `textmode` - Switch back to text mode
- `clear` - Clear display
- `quit` - Exit

### Examples
```
text:Hello World!
color:0,255,0
brightness:100
pattern:rainbow
```

## Protocol

The ESP32 receives commands via serial:
- `FRAME:<768 bytes RGB data>:END` - Display frame
- `BRIGHTNESS:<0-255>\n` - Set brightness
- `CLEAR\n` - Clear display

## Configuration

Edit the LED matrix configuration in `esp32_frame_display.ino`:
- `MATRIX_WIDTH` / `MATRIX_HEIGHT` - Matrix dimensions
- `LED_PIN` - Data pin
- `FLIP_HORIZONTAL` / `FLIP_VERTICAL` - Orientation
- `SERPENTINE_LAYOUT` - Wiring pattern

## Features

- Real-time frame transmission
- Scrolling text with custom colors
- Pattern generation (rainbow, spiral, wave)
- Brightness control
- 15 FPS display updates
- Non-blocking user input