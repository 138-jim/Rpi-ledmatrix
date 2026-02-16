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
                CameraView(bluetoothManager: bluetoothManager)
            }
            .tabItem {
                Label("Camera", systemImage: "camera.fill")
            }

            NavigationView {
                DrawingView(bluetoothManager: bluetoothManager)
            }
            .tabItem {
                Label("Draw", systemImage: "pencil.tip.crop.circle.fill")
            }

            NavigationView {
                SystemMonitorView(bluetoothManager: bluetoothManager)
            }
            .tabItem {
                Label("Monitor", systemImage: "chart.xyaxis.line")
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
