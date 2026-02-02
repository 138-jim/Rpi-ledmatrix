# LED Matrix Bluetooth Bridge

This Bluetooth Low Energy (BLE) bridge service allows iPhone apps to control the LED matrix display wirelessly via Bluetooth.

## Architecture

The bridge acts as a BLE peripheral that exposes control characteristics. It translates BLE commands into HTTP API calls to the existing LED driver web server running on localhost:8080.

```
iPhone App (BLE Central)
    ↓ Bluetooth LE
Raspberry Pi (BLE Peripheral) - This Bridge Service
    ↓ HTTP localhost:8080
LED Driver Web API
    ↓
Display Controller
```

## Installation

Run the installation script as root:

```bash
cd /home/jim/Documents/GitHub/Rpi-ledmatrix
sudo ./bluetooth_bridge/install.sh
```

This will:
1. Install system dependencies (Bluetooth libraries)
2. Install Python dependencies (bless, requests)
3. Enable Bluetooth service
4. Create and install systemd service
5. Optionally enable auto-start on boot
6. Optionally start the service immediately

## Usage

### Service Management

```bash
# Start the service
sudo systemctl start bluetooth-bridge.service

# Stop the service
sudo systemctl stop bluetooth-bridge.service

# Restart the service
sudo systemctl restart bluetooth-bridge.service

# Check status
sudo systemctl status bluetooth-bridge.service

# Enable auto-start on boot
sudo systemctl enable bluetooth-bridge.service

# Disable auto-start
sudo systemctl disable bluetooth-bridge.service

# View logs (follow mode)
sudo journalctl -u bluetooth-bridge.service -f

# View recent logs
sudo journalctl -u bluetooth-bridge.service -n 100
```

### Manual Testing

You can run the server manually for testing:

```bash
cd bluetooth_bridge
sudo python3 ble_server.py
```

Press Ctrl+C to stop.

### Testing with iOS Apps

**LightBlue App** (free on App Store):
1. Download "LightBlue" from the App Store
2. Open the app
3. Scan for devices
4. Look for "LED Matrix" device
5. Connect to it
6. Explore services and characteristics
7. Write test values to characteristics

**Your Custom iPhone App**:
- The app will scan for devices advertising as "LED Matrix"
- Connect using the service UUID: `12345678-1234-5678-1234-56789abcdef0`
- Access characteristics for control

## BLE Protocol

### Service UUID
`12345678-1234-5678-1234-56789abcdef0`

### Characteristics

| Characteristic | UUID | Properties | Format | Description |
|---------------|------|------------|--------|-------------|
| Brightness | ...def1 | Write | 1 byte (0-255) | Set display brightness |
| Pattern | ...def2 | Write | 1 byte (0-36) | Select pattern by index |
| Game Control | ...def3 | Write | 2 bytes | Control games (game_id, action) |
| Status | ...def4 | Read, Notify | JSON string | Get display status |
| Config | ...def5 | Read | JSON string | Get display configuration |
| Power Limit | ...def6 | Write | 2 bytes (uint16) | Set power limit in 0.1A units |
| Sleep Schedule | ...def7 | Write | 4 bytes | Set on/off times (off_h, off_m, on_h, on_m) |
| Frame Stream | ...def8 | Write | Chunked data | Send RGB frame data |

### Pattern Indices (0-36)

See `protocol.py` for the full list of 37 patterns.

Examples:
- 0 = red
- 1 = green
- 14 = rainbow
- 18 = snow
- 33 = elapsed

### Game Indices (0-4)

- 0 = snake
- 1 = pong
- 2 = tictactoe
- 3 = breakout
- 4 = tetris

### Game Actions (0-7)

- 0 = up
- 1 = down
- 2 = left
- 3 = right
- 4 = action (select/fire)
- 5 = reset
- 6 = pause
- 7 = resume

**Special**: To start a game, write `[game_id, 0xFF]` to Game Control characteristic.

### Frame Streaming Protocol

For sending custom images/animations:

1. **Frame Format**: RGB data, row-major order
2. **Size**: 32×32 pixels = 3,072 bytes (width × height × 3)
3. **Chunking**: Frames are split into ~500 byte chunks
4. **Chunk Format**:
   - First 2 bytes: Sequence number (uint16, big-endian)
   - Remaining bytes: Data
   - First chunk also includes 4-byte header: width (2 bytes) + height (2 bytes)
5. **Timeout**: Incomplete frames are discarded after 1 second

Example chunk sequence for 32×32 frame:
- Chunk 0: [0x00, 0x00, width_hi, width_lo, height_hi, height_lo, ...data]
- Chunk 1: [0x00, 0x01, ...data]
- Chunk 2: [0x00, 0x02, ...data]
- ...
- Chunk 6: [0x00, 0x06, ...remaining data]

## Troubleshooting

### Service won't start

Check logs:
```bash
sudo journalctl -u bluetooth-bridge.service -n 50
```

Common issues:
- LED driver not running: Start `led-driver.service` first
- Python dependencies missing: Run `pip3 install -r requirements.txt`
- Bluetooth not enabled: Run `sudo systemctl enable bluetooth && sudo systemctl start bluetooth`

### Can't find device on iPhone

1. Check service is running: `sudo systemctl status bluetooth-bridge.service`
2. Check Bluetooth is enabled: `sudo systemctl status bluetooth`
3. Try restarting: `sudo systemctl restart bluetooth-bridge.service`
4. Check for errors: `sudo journalctl -u bluetooth-bridge.service -f`

### Commands not working

1. Verify LED driver is running: `curl http://localhost:8080/api/status`
2. Check bridge logs: `sudo journalctl -u bluetooth-bridge.service -f`
3. Try manual test: Send test pattern via curl to verify API works

## Files

- `ble_server.py` - Main BLE server implementation
- `protocol.py` - Protocol definitions (UUIDs, mappings, constants)
- `requirements.txt` - Python dependencies
- `install.sh` - Installation script
- `README.md` - This file

## Dependencies

### System Packages
- python3-pip
- python3-dev
- libdbus-1-dev
- libglib2.0-dev
- bluetooth
- bluez
- libbluetooth-dev

### Python Packages
- bless >= 0.2.5 (BLE peripheral library)
- requests >= 2.31.0 (HTTP client)

## Security Notes

- The service runs as root (required for Bluetooth access)
- BLE connection is unencrypted (local range only)
- No authentication/pairing required by default
- Consider adding pairing if needed for your use case

## Performance

- BLE latency: ~20-100ms for simple commands
- Frame streaming: ~10-15 FPS for 32×32 RGB frames
- Status updates: Every 2 seconds (when clients subscribe)

## License

Same as parent project (LED Matrix Controller).
