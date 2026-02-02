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
