# BLE Protocol Quick Reference

This document is a quick reference for iOS app developers implementing the LED Matrix controller.

## Connection

1. **Scan** for BLE peripherals
2. **Look for** device named: `"LED Matrix"`
3. **Connect** to the device
4. **Discover** services with UUID: `12345678-1234-5678-1234-56789abcdef0`
5. **Discover** characteristics within the service

## Service UUID

```
12345678-1234-5678-1234-56789abcdef0
```

## Characteristics

### 1. Brightness Control
- **UUID**: `12345678-1234-5678-1234-56789abcdef1`
- **Properties**: Write
- **Format**: 1 byte (UInt8)
- **Range**: 0-255
- **Example**: `[128]` sets brightness to 50%

### 2. Pattern Selection
- **UUID**: `12345678-1234-5678-1234-56789abcdef2`
- **Properties**: Write
- **Format**: 1 byte (UInt8)
- **Range**: 0-36 (pattern index)
- **Example**: `[14]` displays rainbow pattern

### 3. Game Control
- **UUID**: `12345678-1234-5678-1234-56789abcdef3`
- **Properties**: Write
- **Format**: 2 bytes (game_id, action)
- **Start game**: `[game_id, 0xFF]`
- **Send input**: `[game_id, action_id]`
- **Example**: `[0, 255]` starts Snake, `[0, 0]` sends "up" command

### 4. Status
- **UUID**: `12345678-1234-5678-1234-56789abcdef4`
- **Properties**: Read, Notify
- **Format**: JSON string (UTF-8 encoded)
- **Example response**:
```json
{
  "fps": 30.5,
  "brightness": 128,
  "width": 32,
  "height": 32,
  "led_count": 1024,
  "queue_size": 0
}
```

### 5. Configuration
- **UUID**: `12345678-1234-5678-1234-56789abcdef5`
- **Properties**: Read
- **Format**: JSON string (UTF-8 encoded)
- **Example response**:
```json
{
  "grid": {
    "grid_width": 2,
    "grid_height": 2,
    "panel_width": 16,
    "panel_height": 16
  },
  "panels": [...]
}
```

### 6. Power Limit
- **UUID**: `12345678-1234-5678-1234-56789abcdef6`
- **Properties**: Write
- **Format**: 2 bytes (UInt16, big-endian)
- **Units**: 0.1 Amperes
- **Example**: `[0x00, 0x55]` (85 units) = 8.5A

### 7. Sleep Schedule
- **UUID**: `12345678-1234-5678-1234-56789abcdef7`
- **Properties**: Write
- **Format**: 4 bytes (off_hour, off_min, on_hour, on_min)
- **Example**: `[23, 0, 7, 30]` = off at 23:00, on at 07:30

### 8. Frame Stream
- **UUID**: `12345678-1234-5678-1234-56789abcdef8`
- **Properties**: Write
- **Format**: Chunked RGB data (see below)

## Pattern Index Reference

```swift
// Solid Colors (0-3)
0:  red, 1:  green, 2:  blue, 3:  white

// Geometric (4-8)
4:  corners, 5:  cross, 6:  checkerboard, 7:  grid, 8:  panels

// Animated (9-13)
9:  spiral, 10: wave, 11: fire, 12: plasma, 13: geometric_patterns

// Gradients (14-17)
14: rainbow, 15: color_gradients, 16: gradient_waves, 17: rgb_torch

// Natural (18-26)
18: snow, 19: rain, 20: fireflies, 21: aquarium, 22: ocean_waves
23: northern_lights, 24: starfield, 25: starry_night, 26: fireworks

// Complex (27-32)
27: heart, 28: dna_helix, 29: kaleidoscope, 30: perlin_noise_flow
31: matrix_rain, 32: lava_lamp

// Time-based (33-36)
33: elapsed, 34: sunset_sunrise, 35: sunset_sunrise_loop, 36: dot
```

## Game Index Reference

```swift
0: snake
1: pong
2: tictactoe
3: breakout
4: tetris
```

## Game Action Reference

```swift
0: up
1: down
2: left
3: right
4: action  // Select, fire, etc.
5: reset
6: pause
7: resume
```

## Frame Streaming Protocol

For sending custom images or animations:

### Frame Format
- **Resolution**: 32×32 pixels (or current display size)
- **Color Format**: RGB (3 bytes per pixel)
- **Byte Order**: Row-major (left-to-right, top-to-bottom)
- **Total Size**: 32 × 32 × 3 = 3,072 bytes

### Chunking

Frames must be split into chunks (~500 bytes each):

**Chunk Structure**:
```
[seq_num (2 bytes, big-endian)][data (up to 500 bytes)]
```

**First Chunk** (seq_num = 0):
```
[0x00, 0x00][width_hi, width_lo][height_hi, height_lo][rgb_data...]
```

**Subsequent Chunks**:
```
[seq_hi, seq_lo][rgb_data...]
```

### Swift Example

```swift
import Foundation

func chunkFrame(rgbData: Data, width: Int, height: Int) -> [Data] {
    let maxChunkSize = 500
    var chunks: [Data] = []
    var sequenceNum: UInt16 = 0
    var offset = 0

    // First chunk with header
    var firstChunk = Data()
    firstChunk.append(contentsOf: withUnsafeBytes(of: sequenceNum.bigEndian) { Array($0) })
    firstChunk.append(contentsOf: withUnsafeBytes(of: UInt16(width).bigEndian) { Array($0) })
    firstChunk.append(contentsOf: withUnsafeBytes(of: UInt16(height).bigEndian) { Array($0) })

    let firstChunkDataSize = maxChunkSize - 6  // 2 (seq) + 4 (header)
    let firstData = rgbData.prefix(firstChunkDataSize)
    firstChunk.append(firstData)
    chunks.append(firstChunk)

    offset = firstChunkDataSize
    sequenceNum += 1

    // Remaining chunks
    while offset < rgbData.count {
        var chunk = Data()
        chunk.append(contentsOf: withUnsafeBytes(of: sequenceNum.bigEndian) { Array($0) })

        let chunkDataSize = min(maxChunkSize - 2, rgbData.count - offset)
        let chunkData = rgbData.subdata(in: offset..<(offset + chunkDataSize))
        chunk.append(chunkData)
        chunks.append(chunk)

        offset += chunkDataSize
        sequenceNum += 1
    }

    return chunks
}
```

### Sending Frames

```swift
func sendFrame(rgbData: Data, width: Int, height: Int) {
    let chunks = chunkFrame(rgbData: rgbData, width: width, height: height)

    for chunk in chunks {
        // Write to Frame Stream characteristic
        peripheral.writeValue(chunk,
                            for: frameStreamCharacteristic,
                            type: .withoutResponse)

        // Small delay between chunks to avoid overwhelming BLE buffer
        usleep(5000) // 5ms
    }
}
```

## Swift Code Examples

### Setting Brightness

```swift
func setBrightness(_ value: UInt8) {
    let data = Data([value])
    peripheral.writeValue(data,
                        for: brightnessCharacteristic,
                        type: .withoutResponse)
}
```

### Selecting Pattern

```swift
func setPattern(_ patternIndex: UInt8) {
    let data = Data([patternIndex])
    peripheral.writeValue(data,
                        for: patternCharacteristic,
                        type: .withoutResponse)
}
```

### Starting Game

```swift
func startGame(_ gameIndex: UInt8) {
    let data = Data([gameIndex, 0xFF])
    peripheral.writeValue(data,
                        for: gameControlCharacteristic,
                        type: .withoutResponse)
}
```

### Sending Game Input

```swift
enum GameAction: UInt8 {
    case up = 0, down, left, right
    case action, reset, pause, resume
}

func sendGameInput(_ action: GameAction) {
    // Assuming current game is Snake (index 0)
    let data = Data([0, action.rawValue])
    peripheral.writeValue(data,
                        for: gameControlCharacteristic,
                        type: .withoutResponse)
}
```

### Reading Status

```swift
func readStatus() {
    peripheral.readValue(for: statusCharacteristic)
}

// In CBPeripheralDelegate
func peripheral(_ peripheral: CBPeripheral,
                didUpdateValueFor characteristic: CBCharacteristic,
                error: Error?) {
    guard let data = characteristic.value else { return }

    if characteristic.uuid == statusCharacteristic.uuid {
        if let jsonString = String(data: data, encoding: .utf8),
           let jsonData = jsonString.data(using: .utf8),
           let status = try? JSONDecoder().decode(DisplayStatus.self, from: jsonData) {
            print("FPS: \(status.fps)")
            print("Brightness: \(status.brightness)")
        }
    }
}
```

### Setting Power Limit

```swift
func setPowerLimit(amps: Float) {
    let units = UInt16(amps * 10.0)
    var data = Data()
    data.append(contentsOf: withUnsafeBytes(of: units.bigEndian) { Array($0) })
    peripheral.writeValue(data,
                        for: powerLimitCharacteristic,
                        type: .withoutResponse)
}
```

### Setting Sleep Schedule

```swift
func setSleepSchedule(offHour: UInt8, offMin: UInt8,
                     onHour: UInt8, onMin: UInt8) {
    let data = Data([offHour, offMin, onHour, onMin])
    peripheral.writeValue(data,
                        for: sleepScheduleCharacteristic,
                        type: .withoutResponse)
}
```

## Testing with LightBlue App

1. Download "LightBlue" from the App Store (free)
2. Scan for devices and connect to "LED Matrix"
3. Navigate to service `12345678-...def0`
4. Select a characteristic
5. Write hex values:
   - Brightness: `80` (hex) = 128 (decimal) = 50% brightness
   - Pattern: `0E` (hex) = 14 (decimal) = rainbow pattern
   - Game Start: `00 FF` = Start Snake game
   - Game Input: `00 00` = Snake move up

## Notes

- All multi-byte values use **big-endian** byte order
- Write operations use `.withoutResponse` type for better performance
- Add small delays (5-10ms) between rapid writes
- Status characteristic can be subscribed to for notifications (updates every 2 seconds)
- Frame streaming achieves ~10-15 FPS over BLE for 32×32 frames
- Connection range: typically 10-30 meters
