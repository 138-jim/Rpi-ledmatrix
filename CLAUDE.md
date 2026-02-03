# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Raspberry Pi-based LED matrix control system for WS2812B LED panels. The system uses direct GPIO control via the rpi-ws281x library - no ESP32 or microcontroller required.

**The system is fully implemented** in the `rpi_driver/` directory with:
- Multi-threaded display driver with hot-reload configuration
- FastAPI web server with REST endpoints and WebSocket support
- Multi-protocol frame input (HTTP POST, WebSocket, UDP, named pipe)
- Built-in test patterns and animations
- Power limiting to prevent PSU overload
- Sleep scheduler for automatic on/off times
- System monitoring (temperature, FPS, power draw)
- Auto-updater for git-based deployment

## Quick Start

### Run the driver

```bash
# Setup (first time only)
sudo ./setup_rpi_driver.sh

# Run directly with hardware
sudo python3 -m rpi_driver.main --config configs/current.json

# Run in mock mode (testing without hardware)
python3 -m rpi_driver.main --mock --verbose

# Install as systemd service (runs on boot)
sudo ./install_service.sh

# View service logs
sudo journalctl -u led-driver.service -f
```

### Web interface

Access from any device on your LAN:
- `http://localhost:8080` (from the Pi)
- `http://192.168.1.15:8080` (replace with your Pi's IP)
- `http://raspberrypi.local:8080` (using hostname)

### Send frames from external programs

```python
import numpy as np
import requests

# Create 32x32 frame (for 2x2 grid of 16x16 panels)
frame = np.zeros((32, 32, 3), dtype=np.uint8)
frame[10:20, 10:20] = [255, 0, 0]  # Red square

# Send to display
requests.post('http://raspberrypi.local:8080/api/frame',
              data=frame.tobytes(),
              headers={'Content-Type': 'application/octet-stream'})
```

## System Architecture

### Multi-threaded Design

The system uses several threads that communicate via queues:

1. **Main Thread**: Runs FastAPI web server (uvicorn)
2. **Display Controller Thread** (`display_controller.py`): Main loop that pulls frames from queue, applies coordinate mapping, power limiting, and updates LEDs at target FPS
3. **UDP Receiver Thread** (`frame_receiver.py`): Listens for UDP packets containing frame data
4. **Pipe Receiver Thread** (`frame_receiver.py`): Reads frames from named pipe `/tmp/led_frames.pipe`
5. **Pattern Generator Thread** (`web_api.py`): Generates test patterns on-demand
6. **Sleep Scheduler Thread** (`sleep_scheduler.py`): Checks time and applies on/off schedule
7. **System Monitor Thread** (`system_monitor.py`): Periodically samples CPU temperature and power stats

### Key Components

- **`main.py`**: Entry point that initializes and coordinates all components
- **`led_driver.py`**: Thin wrapper around rpi-ws281x library (or mock for testing)
- **`coordinate_mapper.py`**: Maps virtual 2D frame coordinates to physical LED indices
  - Handles panel positions, rotations (0/90/180/270)
  - Pre-computes lookup tables for fast mapping
  - Supports serpentine (snake) wiring patterns
- **`display_controller.py`**: Main display loop
  - Pulls frames from queue
  - Applies coordinate mapping
  - Applies power limiting
  - Updates LEDs at target FPS
  - Supports hot-reload of configuration
- **`frame_receiver.py`**: Multi-protocol frame input (UDP and named pipe)
- **`web_api.py`**: FastAPI server with REST + WebSocket endpoints
- **`config_manager.py`**: Loads/saves JSON panel configurations
- **`test_patterns.py`**: Built-in patterns (corners, grid, rainbow, scrolling text, etc.)
- **`power_limiter.py`**: Dynamically reduces brightness to stay within current limits
- **`sleep_scheduler.py`**: Automatic on/off at scheduled times
- **`system_monitor.py`**: Monitors CPU temperature and calculates power draw estimates

### Panel Configuration

Panels are defined in JSON files like `configs/current.json`:

```json
{
  "grid": {
    "grid_width": 2,
    "grid_height": 2,
    "panel_width": 16,
    "panel_height": 16,
    "wiring_pattern": "snake"
  },
  "panels": [
    {"id": 0, "rotation": 0, "position": [0, 0]},
    {"id": 1, "rotation": 0, "position": [1, 0]},
    {"id": 2, "rotation": 180, "position": [1, 1]},
    {"id": 3, "rotation": 180, "position": [0, 1]}
  ]
}
```

- `id`: Physical panel order (daisy-chain order on GPIO pin)
- `position`: Logical position in combined display (measured in panels, not pixels)
- `rotation`: Physical panel rotation (0/90/180/270 degrees)
- `wiring_pattern`: How pixels are wired within each panel ("snake", "sequential", "vertical_snake")

### Coordinate Mapping Flow

1. External program generates frame in **virtual coordinates** (e.g., 32x32 for 2x2 grid of 16x16 panels)
2. `CoordinateMapper.map_frame()` converts to **physical LED indices** using pre-computed lookup table
3. Lookup table accounts for:
   - Panel positions in grid
   - Panel rotations
   - Serpentine wiring within panels
   - Display-level rotation (optional)

This allows panels to be physically mounted in any orientation while software sees a simple 2D canvas.

## Development Commands

### Testing

```bash
# Run in mock mode (no hardware required)
python3 -m rpi_driver.main --mock --verbose

# Test specific pattern
curl -X POST http://localhost:8080/api/test-pattern \
  -H "Content-Type: application/json" \
  -d '{"pattern": "corners"}'

# Send test frame via UDP
python3 -c "
import socket, struct, numpy as np
frame = np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)
header = struct.pack('>4sHH', b'LEDF', 32, 32)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(header + frame.tobytes(), ('localhost', 5555))
"
```

### Configuration

```bash
# Generate new panel configuration
python3 configurator.py

# Test configuration without restarting
curl -X POST http://localhost:8080/api/config/reload

# View current configuration
curl http://localhost:8080/api/config
```

### Service Management

```bash
# Start/stop/restart service
sudo systemctl start led-driver.service
sudo systemctl stop led-driver.service
sudo systemctl restart led-driver.service

# Enable/disable auto-start on boot
sudo systemctl enable led-driver.service
sudo systemctl disable led-driver.service

# View logs (follow mode)
sudo journalctl -u led-driver.service -f

# View recent logs
sudo journalctl -u led-driver.service -n 100
```

### Auto-Updater

```bash
# Install auto-updater service (pulls from git and restarts)
sudo ./install_auto_updater.sh

# View auto-updater logs
sudo journalctl -u auto-updater.service -f

# Manual run (for testing)
python3 auto_updater.py --repo-path /home/jim/Esp32-matrix --service led-driver.service
```

## API Endpoints

### REST API

- `GET /api/config` - Get current panel configuration
- `POST /api/config` - Update full configuration (triggers reload)
- `POST /api/config/reload` - Reload config from disk without restart
- `GET /api/panels` - List all panels
- `PUT /api/panels/{id}` - Update single panel (position/rotation)
- `POST /api/frame` - Submit frame (raw RGB bytes: width × height × 3)
- `POST /api/brightness` - Set brightness (0-255)
- `POST /api/test-pattern` - Display test pattern (corners, grid, rainbow, etc.)
- `GET /api/status` - System status (FPS, queue size, brightness, dimensions)
- `GET /api/patterns` - List available test patterns
- `POST /api/sleep-schedule` - Configure auto on/off times
- `GET /api/sleep-schedule` - Get current sleep schedule
- `POST /api/power-limit` - Configure power limiting
- `GET /api/power-limit` - Get current power limit settings
- `GET /api/system-stats` - System monitoring (CPU temp, power draw estimates)

### WebSocket API

- `WS /ws/frames` - Stream frames (binary RGB data)
- `WS /ws/preview` - Receive live preview of displayed frames (JPEG encoded)

## Common Patterns

### Adding a new test pattern

1. Add pattern function to `test_patterns.py`:
```python
def my_pattern(width: int, height: int, frame_number: int) -> np.ndarray:
    """Generate my custom pattern"""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # ... generate pattern ...
    return frame
```

2. Pattern is automatically available via API:
```bash
curl -X POST http://localhost:8080/api/test-pattern \
  -H "Content-Type: application/json" \
  -d '{"pattern": "my_pattern"}'
```

### Sending frames from Python script

```python
import numpy as np
import requests

def send_frame(frame: np.ndarray, host='raspberrypi.local', port=8080):
    """Send frame to LED display"""
    requests.post(f'http://{host}:{port}/api/frame',
                  data=frame.tobytes(),
                  headers={'Content-Type': 'application/octet-stream'})

# Create animation loop
for i in range(100):
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    # ... generate frame ...
    send_frame(frame)
```

### Sending frames via UDP (faster, no HTTP overhead)

```python
import socket
import struct
import numpy as np

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_frame_udp(frame: np.ndarray, host='raspberrypi.local', port=5555):
    """Send frame via UDP"""
    height, width = frame.shape[:2]
    header = struct.pack('>4sHH', b'LEDF', width, height)
    packet = header + frame.tobytes()
    sock.sendto(packet, (host, port))
```

### Hot-reloading configuration

The display controller automatically reloads configuration when signaled:

```bash
# Trigger reload via API
curl -X POST http://localhost:8080/api/config/reload

# Or update and reload in one call
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d @configs/new_config.json
```

During reload:
1. Display is cleared
2. New configuration is loaded
3. Coordinate mapper rebuilds lookup tables
4. Display resumes with new mapping

No need to restart the service.

## Hardware Notes

### GPIO Connection

- **GPIO 18 (Pin 12)**: PWM0 - Default pin for LED data line
- **GND**: Must be common between Pi and LED power supply
- **External 5V PSU**: Required for LED power (do NOT power from Pi)

### Power Considerations

- WS2812B LEDs draw up to 60mA per LED at full white
- 4× 16×16 panels = 1024 LEDs = 61.4A theoretical max
- Power limiter (enabled by default) reduces brightness to stay within PSU limits
- Default limit: 80A (configurable via API)

### Troubleshooting

**"Failed to create mailbox device" or permission errors:**
```bash
sudo usermod -a -G gpio $USER
# Then logout and login
```

**"Permission denied" even after gpio group:**
```bash
# Run with sudo (rpi-ws281x requires root for DMA access)
sudo python3 -m rpi_driver.main
```

**LEDs show wrong colors:**
- Check LED strip type in `led_driver.py` (GRB vs RGB)
- Default is GRB (0x00081000) for WS2812B

**Flickering or glitching:**
```bash
# Disable onboard audio (conflicts with PWM)
echo "dtparam=audio=off" | sudo tee -a /boot/config.txt
sudo reboot
```

**Panels in wrong position:**
- Use test pattern "corners" to identify panel order
- Adjust `rotation` in web interface or config file
- Verify `wiring_pattern` matches physical wiring

## File Structure

```
rpi_driver/              - Main driver package
├── main.py             - Entry point, orchestrates all components
├── led_driver.py       - rpi-ws281x wrapper (+ mock for testing)
├── coordinate_mapper.py - Virtual→physical coordinate mapping
├── display_controller.py - Main display loop (threaded)
├── frame_receiver.py   - UDP and named pipe input
├── web_api.py          - FastAPI REST + WebSocket server
├── config_manager.py   - JSON config loading/saving
├── test_patterns.py    - Built-in patterns and animations
├── power_limiter.py    - Dynamic brightness limiting
├── sleep_scheduler.py  - Auto on/off scheduling
├── system_monitor.py   - CPU temp and power monitoring
├── fluid_simulation.py - Physics-based fluid animation
└── simple_lava_lamp.py - Lava lamp effect

configs/                - Panel configurations
├── current.json        - Active configuration
└── *.json              - Other saved configs

static/                 - Web UI assets
├── index.html          - Web interface
└── app.js              - Web interface logic

*.sh                    - Installation scripts
configurator.py         - Interactive panel config generator
auto_updater.py         - Git-based auto-deploy script
requirements.txt        - Python dependencies
```
