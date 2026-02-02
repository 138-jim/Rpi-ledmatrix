# LED Matrix Controller - iOS App

This directory contains Swift template files for building the iPhone LED Matrix Controller app.

## What's Been Created

✅ **Complete Files (Ready to Use)**:
- `Services/Protocol.swift` - BLE protocol constants and UUIDs
- `Services/BluetoothManager.swift` - Complete CoreBluetooth implementation
- `Models/DisplayPattern.swift` - All 37 patterns with categories
- `Models/Game.swift` - 5 games with metadata
- `Models/DisplayStatus.swift` - Status and configuration models
- `Models/LEDDisplayConfig.swift` - Display configuration
- `Utils/FrameChunker.swift` - Frame chunking for BLE
- `Utils/ImageProcessor.swift` - Image processing utilities
- `Views/HomeView.swift` - Main dashboard (complete and working!)

## Getting Started with Xcode

### Step 1: Create Xcode Project

1. Open **Xcode**
2. File → New → Project
3. Choose **iOS** → **App**
4. Configuration:
   - Product Name: `LEDMatrixController`
   - Interface: **SwiftUI**
   - Language: **Swift**
   - Organization Identifier: `com.yourname`
5. Save to: `/Users/jim/Documents/GitHub/Rpi-ledmatrix/ios-app/LEDMatrixController`

### Step 2: Configure Capabilities

1. Select project in navigator (blue icon)
2. Select **LEDMatrixController** target
3. **Signing & Capabilities** tab:
   - Click **+ Capability**
   - Add **Background Modes**
   - Check "Uses Bluetooth LE accessories"

### Step 3: Configure Info.plist

1. Find **Info.plist** in navigator
2. Right-click → Open As → Source Code
3. Add before `</dict>`:

```xml
<key>NSBluetoothAlwaysUsageDescription</key>
<string>Control your LED display via Bluetooth</string>
<key>NSCameraUsageDescription</key>
<string>Stream camera to LED display</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>Display photos on LED matrix</string>
```

### Step 4: Create Folder Structure

In Xcode, create these **Groups** (File → New → Group):
- App
- Models
- Services
- Views
- Components
- Utils

### Step 5: Copy Template Files

For each file in `templates/`, create a new Swift file in Xcode and copy the contents:

**Example for BluetoothManager.swift**:
1. Right-click **Services** folder in Xcode
2. New File → Swift File
3. Name it `BluetoothManager.swift`
4. Copy contents from `templates/Services/BluetoothManager.swift`
5. Paste into Xcode

Repeat for all files in templates/ directory.

### Step 6: Create ContentView (App Entry Point)

Replace the default `ContentView.swift` with:

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

            NavigationView {
                PatternsView(bluetoothManager: bluetoothManager)
            }
            .tabItem {
                Label("Patterns", systemImage: "paintpalette.fill")
            }

            NavigationView {
                GamesView(bluetoothManager: bluetoothManager)
            }
            .tabItem {
                Label("Games", systemImage: "gamecontroller.fill")
            }

            NavigationView {
                SettingsView(bluetoothManager: bluetoothManager)
            }
            .tabItem {
                Label("Settings", systemImage: "gearshape.fill")
            }
        }
    }
}
```

### Step 7: Run on iPhone

1. Connect iPhone via USB
2. Trust computer on iPhone
3. Select your iPhone in device dropdown (top center)
4. Click Play button (▶️) or Cmd+R
5. On iPhone: Settings → General → VPN & Device Management → Trust your Apple ID
6. Run again from Xcode

## Remaining Files to Create

I've created the core files. You'll need to add these simpler views:

### PatternsView.swift (Simple Version)

```swift
import SwiftUI

struct PatternsView: View {
    @ObservedObject var bluetoothManager: BluetoothManager

    var body: some View {
        List {
            ForEach(PatternCategory.allCases, id: \.self) { category in
                Section(header: Text(category.rawValue)) {
                    ForEach(DisplayPattern.categorized[category] ?? [], id: \.id) { pattern in
                        Button(action: {
                            bluetoothManager.setPattern(UInt8(pattern.id))
                        }) {
                            HStack {
                                Text(pattern.name)
                                    .font(.body)
                                Spacer()
                                Text(pattern.description)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Patterns")
        .disabled(!bluetoothManager.isConnected)
    }
}
```

### GamesView.swift (Simple Version)

```swift
import SwiftUI

struct GamesView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @State private var showingGameController = false

    var body: some View {
        List(Game.allGames) { game in
            Button(action: {
                bluetoothManager.startGame(UInt8(game.id))
                showingGameController = true
            }) {
                HStack {
                    Image(systemName: game.icon)
                        .font(.largeTitle)
                        .foregroundColor(.blue)
                        .frame(width: 60)

                    VStack(alignment: .leading) {
                        Text(game.displayName)
                            .font(.headline)
                        Text(game.description)
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }

                    Spacer()

                    Image(systemName: "play.circle.fill")
                        .foregroundColor(.green)
                }
            }
        }
        .navigationTitle("Games")
        .disabled(!bluetoothManager.isConnected)
        .sheet(isPresented: $showingGameController) {
            GameControllerView(bluetoothManager: bluetoothManager)
        }
    }
}
```

### GameControllerView.swift (D-Pad)

```swift
import SwiftUI

struct GameControllerView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @Environment(\.dismiss) var dismiss

    var body: some View {
        VStack(spacing: 40) {
            Text("Game Controller")
                .font(.largeTitle)
                .bold()

            Spacer()

            // D-Pad
            VStack(spacing: 10) {
                // Up button
                GameButton(icon: "arrowtriangle.up.fill") {
                    bluetoothManager.sendGameInput(.up)
                }

                HStack(spacing: 10) {
                    // Left button
                    GameButton(icon: "arrowtriangle.left.fill") {
                        bluetoothManager.sendGameInput(.left)
                    }

                    // Center action button
                    GameButton(icon: "circle.fill", color: .green) {
                        bluetoothManager.sendGameInput(.action)
                    }

                    // Right button
                    GameButton(icon: "arrowtriangle.right.fill") {
                        bluetoothManager.sendGameInput(.right)
                    }
                }

                // Down button
                GameButton(icon: "arrowtriangle.down.fill") {
                    bluetoothManager.sendGameInput(.down)
                }
            }

            Spacer()

            // Control buttons
            HStack(spacing: 20) {
                Button(action: {
                    bluetoothManager.sendGameInput(.reset)
                }) {
                    Label("Reset", systemImage: "arrow.clockwise")
                        .padding()
                        .background(Color.orange)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }

                Button(action: {
                    bluetoothManager.sendGameInput(.pause)
                }) {
                    Label("Pause", systemImage: "pause.fill")
                        .padding()
                        .background(Color.blue)
                        .foregroundColor(.white)
                        .cornerRadius(10)
                }
            }

            Button("Done") {
                dismiss()
            }
            .font(.headline)
        }
        .padding()
    }
}

struct GameButton: View {
    let icon: String
    var color: Color = .blue
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: icon)
                .font(.system(size: 40))
                .foregroundColor(.white)
                .frame(width: 80, height: 80)
                .background(color)
                .cornerRadius(15)
        }
    }
}
```

### SettingsView.swift (Basic)

```swift
import SwiftUI

struct SettingsView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @State private var powerLimit: Double = 8.5

    var body: some View {
        Form {
            Section("Connection") {
                if bluetoothManager.isConnected {
                    Text("Connected to LED Matrix")
                        .foregroundColor(.green)
                    Button("Disconnect", role: .destructive) {
                        bluetoothManager.disconnect()
                    }
                } else {
                    Text("Not connected")
                        .foregroundColor(.secondary)
                    Button("Scan for Devices") {
                        bluetoothManager.startScanning()
                    }
                }
            }

            Section("Power Management") {
                HStack {
                    Text("Power Limit")
                    Spacer()
                    Text("\(powerLimit, specifier: "%.1f")A")
                        .foregroundColor(.secondary)
                }
                Slider(value: $powerLimit, in: 1...15, step: 0.5)
                    .onChange(of: powerLimit) { newValue in
                        bluetoothManager.setPowerLimit(amps: Float(newValue))
                    }
                    .disabled(!bluetoothManager.isConnected)
            }

            Section("Display Info") {
                if let config = bluetoothManager.displayConfig {
                    HStack {
                        Text("Resolution")
                        Spacer()
                        Text("\(config.grid.totalWidth)×\(config.grid.totalHeight)")
                    }
                    HStack {
                        Text("Panels")
                        Spacer()
                        Text("\(config.panels.count)")
                    }
                }
            }

            Section("About") {
                HStack {
                    Text("Version")
                    Spacer()
                    Text("1.0.0")
                        .foregroundColor(.secondary)
                }
            }
        }
        .navigationTitle("Settings")
    }
}
```

## Testing Your App

### Phase 1: Test Without Hardware

1. Build and run on iPhone
2. Navigate through tabs
3. Verify UI looks correct
4. Check that Bluetooth permission prompt appears

### Phase 2: Test with Hardware

1. Ensure Bluetooth bridge is running on Pi:
   ```bash
   sudo systemctl status bluetooth-bridge.service
   ```

2. In app:
   - Tap "Scan" on Home tab
   - Should see "LED Matrix" device
   - Tap to connect

3. Test controls:
   - Adjust brightness slider → LEDs should dim/brighten
   - Go to Patterns tab → Select "rainbow" → Should show rainbow
   - Go to Games tab → Start Snake → Use D-pad

## Troubleshooting

### "Bluetooth is not available"
- Go to iPhone Settings → Privacy & Security → Bluetooth
- Enable for LEDMatrixController

### Can't find "LED Matrix" device
- Check Pi: `sudo systemctl status bluetooth-bridge.service`
- Restart bridge: `sudo systemctl restart bluetooth-bridge.service`
- Check Pi Bluetooth: `sudo systemctl status bluetooth`

### App crashes when connecting
- Check Xcode console for errors
- Verify all template files were copied correctly
- Ensure Info.plist has Bluetooth permission string

### Pattern/game commands don't work
- Check Pi logs: `sudo journalctl -u bluetooth-bridge.service -f`
- Verify LED driver is running: `sudo systemctl status led-driver.service`

## Next Steps

After basic testing works:

1. **Add Custom Content View** - For photos, camera, drawing
2. **Polish UI** - Add animations, better layouts
3. **Error Handling** - Show alerts for connection failures
4. **Persistence** - Remember last connected device
5. **Frame Streaming** - Implement photo/camera features

## Resources

- **Swift Documentation**: https://docs.swift.org/swift-book/
- **SwiftUI Tutorials**: https://developer.apple.com/tutorials/swiftui
- **CoreBluetooth Guide**: https://developer.apple.com/documentation/corebluetooth
- **Hacking with Swift**: https://www.hackingwithswift.com/100/swiftui

## File Checklist

Copy these files from `templates/` to your Xcode project:

**Services/** (2 files):
- [x] Protocol.swift
- [x] BluetoothManager.swift

**Models/** (4 files):
- [x] DisplayPattern.swift
- [x] Game.swift
- [x] DisplayStatus.swift
- [x] LEDDisplayConfig.swift

**Utils/** (2 files):
- [x] FrameChunker.swift
- [x] ImageProcessor.swift

**Views/** (5 files):
- [x] HomeView.swift
- [ ] PatternsView.swift (code above)
- [ ] GamesView.swift (code above)
- [ ] GameControllerView.swift (code above)
- [ ] SettingsView.swift (code above)

**App/**:
- [ ] ContentView.swift (modified, code above)

## Questions?

If you encounter issues:
1. Check this README
2. Review Xcode console for error messages
3. Check Pi bridge logs
4. Verify all files are in correct groups in Xcode

Happy coding! 🎉
