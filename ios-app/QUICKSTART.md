# Quick Start Guide - iOS App

## What You Have Now

✅ **Bluetooth Bridge** - Running on Raspberry Pi, advertising as "LED Matrix"
✅ **iOS App Templates** - All core Swift files ready to use
✅ **Complete README** - Detailed setup instructions

## 5-Minute Setup

### 1. Create Xcode Project (2 minutes)

```
Open Xcode
→ Create new Project
→ iOS App
→ Name: LEDMatrixController
→ Interface: SwiftUI
→ Save to: /Users/jim/Documents/GitHub/Rpi-ledmatrix/ios-app/
```

### 2. Configure Permissions (1 minute)

Add to **Info.plist**:
```xml
<key>NSBluetoothAlwaysUsageDescription</key>
<string>Control LED display via Bluetooth</string>
```

Enable **Background Modes** → Check "Uses Bluetooth LE accessories"

### 3. Copy Template Files (2 minutes)

In Xcode, create folders:
- Models, Services, Views, Utils

For each `.swift` file in `templates/`, create matching file in Xcode and copy contents.

**Critical files**:
1. `Services/Protocol.swift` - BLE UUIDs ✅
2. `Services/BluetoothManager.swift` - Bluetooth logic ✅
3. `Models/DisplayPattern.swift` - 37 patterns ✅
4. `Views/HomeView.swift` - Main UI ✅

### 4. Update ContentView.swift

Replace with:
```swift
import SwiftUI

struct ContentView: View {
    @StateObject private var bluetoothManager = BluetoothManager()

    var body: some View {
        TabView {
            NavigationView {
                HomeView(bluetoothManager: bluetoothManager)
            }
            .tabItem {
                Label("Home", systemImage: "house.fill")
            }
        }
    }
}
```

### 5. Build & Test

1. Connect iPhone via USB
2. Select iPhone in Xcode (top center)
3. Click ▶️ (or Cmd+R)
4. On iPhone: Settings → Trust Developer
5. Run again

## Testing

### First Run (Without Pi)
- App should launch
- Shows "Not Connected"
- Can navigate UI
- Bluetooth permission prompt appears

### With Raspberry Pi
1. On Pi: `sudo systemctl status bluetooth-bridge.service` (should be active)
2. In app: Tap "Scan"
3. Should see "LED Matrix"
4. Tap to connect
5. Try brightness slider → LEDs should respond!

## Minimal Working App

If you want the absolute minimum to test Bluetooth:

**Just copy these 4 files**:
1. `Services/Protocol.swift`
2. `Services/BluetoothManager.swift`
3. `Models/DisplayStatus.swift`
4. `Views/HomeView.swift`

Then use the ContentView above. That's it!

## Next Steps

Once basic connection works:

1. **Add PatternsView** - Code in README.md
2. **Add GamesView** - Code in README.md
3. **Test patterns** - Select "rainbow", "fire", etc.
4. **Test games** - Start Snake, use D-pad

## Common Issues

**"Bluetooth not available"**
→ Add Bluetooth permission to Info.plist

**Can't find device**
→ Check Pi: `sudo systemctl restart bluetooth-bridge.service`

**Build errors**
→ Ensure all imports are at top of files
→ Check file is in correct Xcode group

**Connection fails**
→ Check Pi logs: `sudo journalctl -u bluetooth-bridge.service -f`

## File Summary

**Templates provided** (9 files):
- ✅ 2 Service files (BluetoothManager, Protocol)
- ✅ 4 Model files (Pattern, Game, Status, Config)
- ✅ 2 Utility files (FrameChunker, ImageProcessor)
- ✅ 1 View file (HomeView - complete dashboard)

**You need to create** (4 simple files):
- PatternsView.swift (code in README)
- GamesView.swift (code in README)
- GameControllerView.swift (code in README)
- SettingsView.swift (code in README)

**Total time**: 15-20 minutes to get a working app!

## Help

Stuck? Check:
1. `README.md` - Full instructions
2. Xcode console - Error messages
3. Pi logs - `sudo journalctl -u bluetooth-bridge.service -f`

The app is designed to work with minimal setup. The hard parts (Bluetooth, protocol, chunking) are done!
