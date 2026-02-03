# iPhone App Integration Guide

## Dynamic Pattern List Feature

The BLE server now supports dynamic pattern discovery, so the iPhone app doesn't need to be updated every time a new pattern is added.

### New Characteristic

**Pattern List Characteristic (Read)**
- **UUID**: `12345678-1234-5678-1234-56789abcdef9`
- **Permission**: Read
- **Format**: JSON string

### JSON Response Format

```json
{
  "patterns": [
    "red",
    "green",
    "blue",
    "white",
    "corners",
    "cross",
    "checkerboard",
    "grid",
    "panels",
    "spiral",
    "wave",
    "fire",
    "plasma",
    ...
  ],
  "count": 37
}
```

### Implementation Steps for iPhone App

1. **On Connection**: Read the Pattern List characteristic to get the current available patterns

```swift
// Read pattern list characteristic
let patternListUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef9")

func peripheral(_ peripheral: CBPeripheral,
                didDiscoverCharacteristicsFor service: CBService,
                error: Error?) {
    guard let characteristics = service.characteristics else { return }

    for characteristic in characteristics {
        if characteristic.uuid == patternListUUID {
            peripheral.readValue(for: characteristic)
        }
    }
}

func peripheral(_ peripheral: CBPeripheral,
                didUpdateValueFor characteristic: CBCharacteristic,
                error: Error?) {
    if characteristic.uuid == patternListUUID {
        guard let data = characteristic.value else { return }

        // Parse JSON
        if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let patterns = json["patterns"] as? [String],
           let count = json["count"] as? Int {

            // Update UI with available patterns
            self.availablePatterns = patterns
            print("Loaded \(count) patterns from device")
        }
    }
}
```

2. **Display in UI**: Show the pattern list in a picker/list view

3. **Send Pattern**: Use the existing Pattern characteristic with the index

```swift
// Send pattern index (0-based)
let patternIndex: UInt8 = 5  // Example: "cross"
let data = Data([patternIndex])
peripheral.writeValue(data,
                     for: patternCharacteristic,
                     type: .withResponse)
```

### Benefits

- **No app updates needed**: When new patterns are added to the Raspberry Pi, the iPhone app automatically sees them
- **Always in sync**: Pattern list is fetched from the device, ensuring compatibility
- **Future-proof**: Easy to add new patterns without coordinating app releases

### Optional: Game List Support

A similar characteristic for games can be added using `get_game_list_json()`:

```json
{
  "games": ["snake", "pong", "tictactoe", "breakout", "tetris"],
  "count": 5
}
```

This would use UUID `12345678-1234-5678-1234-56789abcdefa` (next in sequence).

### Testing with Windows Controller

The Windows controller script has been updated to demonstrate this feature:

```bash
python bluetooth_bridge/windows_controller.py
```

Choose option `9` to fetch and display patterns from the device.

### Backward Compatibility

The existing Pattern characteristic (UUID `12345678-1234-5678-1234-56789abcdef2`) still works the same way:
- Write a single byte (0-255) representing the pattern index
- The pattern names remain the same

This is purely an additive feature - existing apps will continue to work.
