# Dynamic Pattern List - iOS App Changes

## Overview
The iOS app now automatically fetches and displays the available patterns from the Raspberry Pi device, eliminating the need to update the app when new patterns are added.

## Files Modified

### 1. `Services/Protocol.swift`
- **Added**: `patternListUUID` constant for the new characteristic
- **Added**: `PatternListResponse` struct to decode JSON response from device
  ```swift
  static let patternListUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef9")

  struct PatternListResponse: Codable {
      let patterns: [String]
      let count: Int
  }
  ```

### 2. `Services/BluetoothManager.swift`
- **Added**: `@Published var availablePatterns: [String] = []` - stores dynamic patterns from device
- **Added**: `patternListCharacteristic` reference
- **Added**: `requestPatternList()` method to manually fetch patterns
- **Modified**: Connection flow to automatically read pattern list on connection
- **Modified**: Characteristic discovery to handle pattern list UUID
- **Modified**: `didUpdateValueFor` to parse pattern list JSON response
- **Modified**: Disconnect flow to clear `availablePatterns`

### 3. `Models/DisplayPattern.swift`
- **Added**: `createDynamicPatterns(from:)` - creates DisplayPattern objects from device pattern names
  - Matches with existing patterns to preserve category and description
  - Creates new patterns with generic info for unknown patterns
- **Added**: `categorizeDynamic(_:)` - categorizes dynamic patterns for UI display

### 4. `Views/PatternsView.swift`
- **Modified**: Now displays dynamic patterns when available, falls back to built-in list
- **Added**: Status indicator showing pattern source (device vs built-in)
- **Added**: Refresh button when connected but no dynamic patterns loaded
- **Features**:
  - Green antenna icon when using device patterns
  - Orange computer icon when using built-in patterns
  - Pattern count display
  - Manual refresh option

## How It Works

### Connection Flow
1. **App connects** to LED Matrix device via Bluetooth
2. **Discovers characteristics** including the new Pattern List characteristic
3. **Automatically reads** pattern list characteristic on connection
4. **Parses JSON** response: `{"patterns": [...], "count": 37}`
5. **Updates UI** - PatternsView automatically shows device patterns
6. **Maintains IDs** - pattern indices match between device and app

### Fallback Behavior
- If device doesn't support pattern list characteristic: Uses built-in list
- If connection fails: Uses built-in list
- If JSON parsing fails: Uses built-in list
- **Seamless user experience** - app works with old and new devices

### Pattern Matching
When device sends pattern names:
1. **Check built-in list** - if pattern name matches, use its category/description
2. **Create new pattern** - if name is unknown, create with default category
3. **Preserve order** - pattern index matches device's pattern array

## Testing

### With Device Support
1. Connect to LED Matrix device
2. Check for green antenna icon in Patterns view
3. Verify pattern count matches device
4. Select any pattern - should work correctly

### Without Device Support (Old Firmware)
1. Connect to LED Matrix device
2. Orange computer icon shows "Using built-in pattern list"
3. Built-in 37 patterns display normally
4. App functions normally with hardcoded patterns

### Manual Refresh
1. Connect to device
2. If orange icon shows, tap "Refresh" button
3. Should attempt to fetch patterns from device

## Benefits

✅ **No app updates needed** - add patterns on Pi, app sees them automatically
✅ **Always in sync** - app displays exactly what device supports
✅ **Backward compatible** - works with old firmware using built-in list
✅ **Visual feedback** - clear indicator of pattern source
✅ **Graceful fallback** - seamless experience on connection/parsing failures

## Future Enhancements

Possible additions:
- Game list dynamic loading (similar implementation)
- Pattern categories from device
- Pattern descriptions from device
- Pattern preview thumbnails from device
