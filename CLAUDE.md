# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is an ESP32 LED matrix control system with multiple deployment configurations:
- **ESP32 Hardware**: Two Arduino sketches for different use cases
- **Raspberry Pi Controller**: Python-based frame renderer and serial communicator 
- **Cross-platform Testing**: Windows-compatible version with GUI mock display
- **Auto-updater**: Git-based automatic deployment system for Raspberry Pi

## Architecture

The system uses a distributed architecture where different components handle specific responsibilities:

### ESP32 Firmware
- `esp32_frame_display/esp32_frame_display.ino`: Serial-controlled frame display (works with Raspberry Pi)
- `esp32_multi_panel_display/esp32_multi_panel_display.ino`: Enhanced version supporting dynamic panel configurations and variable frame sizes

### Python Controllers
- `led_matrix_controller.py`: Main Raspberry Pi controller with text rendering and pattern generation
- `led_matrix_controller_windows_test.py`: Cross-platform version with mock display capabilities
- `rpi_led_controller.py`: Simplified ESP32 communication wrapper
- `test_mock_display.py`: Testing utilities for mock display functionality
- `auto_updater.py`: Git-based automatic deployment system

### Communication Protocol
ESP32 receives serial commands:

**Standard Protocol** (single 16x16 panel):
- `FRAME:<768 bytes RGB data>:END` - Display 16x16 RGB frame
- `BRIGHTNESS:<0-255>\n` - Set LED brightness
- `CLEAR\n` - Clear display

**Enhanced Multi-Panel Protocol**:
- `CONFIG:width,height\n` - Configure total display dimensions
- `FRAME:size:<variable bytes RGB data>:END` - Display frame with specified size
- `STATUS\n` - Get current configuration and status
- `INFO\n` - Show available commands

## Development Commands

### Python Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Or use the provided setup scripts
./install_dependencies.sh    # Basic installation
./setup_rpi.sh              # Raspberry Pi specific setup
```

### Running Controllers
```bash
# Main Raspberry Pi controller with ESP32 hardware
python3 led_matrix_controller.py

# Simplified ESP32 communication wrapper  
python3 rpi_led_controller.py

# Cross-platform testing with mock GUI display
python3 led_matrix_controller_windows_test.py --mock --gui

# Cross-platform testing with ASCII output
python3 led_matrix_controller_windows_test.py --mock --ascii

# Test mock display functionality
python3 test_mock_display.py
```

### Hardware Setup
1. Upload Arduino sketch to ESP32:
   - Use `esp32_frame_display/esp32_frame_display.ino` for basic serial control
   - Use `esp32_multi_panel_display/esp32_multi_panel_display.ino` for enhanced multi-panel support
2. Connect ESP32 to Raspberry Pi via USB
3. Run setup script: `./setup_rpi.sh` 
4. Logout/login for serial permissions
5. Find ESP32 port: `ls /dev/tty*` (usually `/dev/ttyUSB0` or `/dev/ttyACM0`)


### Auto-updater System
```bash
# Install as systemd service (Raspberry Pi)
sudo ./install_updater.sh

# Manual run
python3 auto_updater.py
```

## Key Configuration Points

### ESP32 Hardware Settings
In Arduino sketches, configure:
- `LED_PIN`: GPIO pin for LED data (default: 26)
- `MATRIX_WIDTH/HEIGHT`: Display dimensions (default: 16x16)
- `FLIP_HORIZONTAL/VERTICAL`: Orientation adjustments
- `SERPENTINE_LAYOUT`: Wiring pattern (zigzag vs row-by-row)


### Raspberry Pi Integration
The auto-updater monitors git repository changes and restarts the controller automatically. Default paths in `auto_updater.py`:
- Repository: `/home/jim/Esp32-matrix`
- Target script: `led_matrix_controller.py`
- Check interval: 30 seconds

## Testing and Mock Mode

The Windows-compatible version includes comprehensive testing capabilities:
- `--mock`: Enable software-only mode (no serial hardware required)
- `--gui`: Tkinter-based visual LED matrix simulator  
- `--ascii`: Console-based matrix display with Unicode blocks
- `--port`: Specify serial port (auto-detects COM3 on Windows, /dev/ttyUSB0 on Linux)

Mock mode supports all controller features including scrolling text, patterns (rainbow, spiral, wave), and brightness control.

## Serial Communication

Hardware controllers expect specific serial configuration:
- Baud rate: 115200
- Port: `/dev/ttyUSB0` (Raspberry Pi), `COM3` (Windows)
- Frame format: Binary RGB data in serpentine layout for LED strips


## Dependencies

### Python Requirements
- `pyserial>=3.5`: Serial communication with ESP32
- `numpy>=1.19.0`: Matrix operations and frame buffering  
- `Pillow>=8.0.0`: Text rendering and image processing
- `tkinter`: GUI interface (usually included with Python)

### Arduino Libraries
- `FastLED`: LED strip control