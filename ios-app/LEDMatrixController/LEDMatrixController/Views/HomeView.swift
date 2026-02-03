//
//  HomeView.swift
//  LEDMatrixController
//
//  Main dashboard view
//

import SwiftUI
import CoreBluetooth

struct HomeView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @State private var brightness: Double = 128

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Connection Status
                ConnectionStatusCard(isConnected: bluetoothManager.isConnected)

                if bluetoothManager.isConnected {
                    // Brightness Control
                    BrightnessControl(
                        brightness: $brightness,
                        onChange: { newValue in
                            bluetoothManager.setBrightness(UInt8(newValue))
                        }
                    )

                    // Display Status
                    if let status = bluetoothManager.displayStatus {
                        DisplayStatusCard(status: status)
                    }

                    // Quick Actions
                    QuickActionsCard(bluetoothManager: bluetoothManager)
                }
            }
            .padding()
        }
        .navigationTitle("LED Matrix")
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                if !bluetoothManager.isConnected {
                    Button("Scan") {
                        bluetoothManager.startScanning()
                    }
                } else {
                    Button("Disconnect") {
                        bluetoothManager.disconnect()
                    }
                    .foregroundColor(.red)
                }
            }
        }
        .sheet(isPresented: $bluetoothManager.isScanning) {
            DeviceScannerView(bluetoothManager: bluetoothManager)
        }
    }
}

// MARK: - Connection Status Card

struct ConnectionStatusCard: View {
    let isConnected: Bool

    var body: some View {
        HStack {
            Image(systemName: isConnected ? "checkmark.circle.fill" : "exclamationmark.circle.fill")
                .font(.title)
                .foregroundColor(isConnected ? .green : .orange)

            VStack(alignment: .leading) {
                Text(isConnected ? "Connected" : "Not Connected")
                    .font(.headline)
                Text(isConnected ? "LED Matrix ready" : "Tap Scan to find devices")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            Spacer()
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

// MARK: - Brightness Control

struct BrightnessControl: View {
    @Binding var brightness: Double
    let onChange: (Double) -> Void

    @State private var debounceWorkItem: DispatchWorkItem?

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Image(systemName: "sun.max.fill")
                Text("Brightness")
                    .font(.headline)
                Spacer()
                Text("\(Int(brightness))")
                    .foregroundColor(.secondary)
            }

            Slider(value: $brightness, in: 0...255, step: 1)
                .onChange(of: brightness) { oldValue, newValue in
                    // Cancel previous debounce timer
                    debounceWorkItem?.cancel()

                    // Create new debounce timer
                    let workItem = DispatchWorkItem {
                        onChange(newValue)
                    }
                    debounceWorkItem = workItem

                    // Execute after 150ms delay
                    DispatchQueue.main.asyncAfter(deadline: .now() + 0.15, execute: workItem)
                }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

// MARK: - Display Status Card

struct DisplayStatusCard: View {
    let status: DisplayStatus

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Display Status")
                .font(.headline)

            Divider()

            HStack {
                StatusRow(icon: "speedometer", label: "FPS", value: String(format: "%.1f", status.fps))
                Spacer()
                StatusRow(icon: "square.grid.2x2", label: "Size", value: "\(status.width)×\(status.height)")
            }

            HStack {
                StatusRow(icon: "lightbulb.fill", label: "LEDs", value: "\(status.ledCount)")
                Spacer()
                if let temp = status.temperature {
                    StatusRow(icon: "thermometer", label: "Temp", value: String(format: "%.1f°C", temp))
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

struct StatusRow: View {
    let icon: String
    let label: String
    let value: String

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .foregroundColor(.blue)
                .frame(width: 20)
            VStack(alignment: .leading) {
                Text(label)
                    .font(.caption)
                    .foregroundColor(.secondary)
                Text(value)
                    .font(.body)
                    .bold()
            }
        }
    }
}

// MARK: - Quick Actions Card

struct QuickActionsCard: View {
    @ObservedObject var bluetoothManager: BluetoothManager

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text("Quick Actions")
                .font(.headline)

            Divider()

            LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 10) {
                QuickActionButton(icon: "paintpalette.fill", title: "Rainbow", color: .purple) {
                    bluetoothManager.setPattern(14)  // Rainbow pattern
                }

                QuickActionButton(icon: "flame.fill", title: "Fire", color: .orange) {
                    bluetoothManager.setPattern(11)  // Fire pattern
                }

                QuickActionButton(icon: "snowflake", title: "Snow", color: .blue) {
                    bluetoothManager.setPattern(18)  // Snow pattern
                }

                QuickActionButton(icon: "gamecontroller.fill", title: "Snake", color: .green) {
                    bluetoothManager.startGame(0)  // Snake game
                }
            }
        }
        .padding()
        .background(Color(.systemBackground))
        .cornerRadius(12)
        .shadow(radius: 2)
    }
}

struct QuickActionButton: View {
    let icon: String
    let title: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack {
                Image(systemName: icon)
                    .font(.title2)
                    .foregroundColor(color)
                Text(title)
                    .font(.caption)
                    .foregroundColor(.primary)
            }
            .frame(height: 70)
            .frame(maxWidth: .infinity)
            .background(Color(.secondarySystemBackground))
            .cornerRadius(10)
        }
    }
}

// MARK: - Device Scanner View

struct DeviceScannerView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @Environment(\.dismiss) var dismiss

    var body: some View {
        NavigationView {
            List(bluetoothManager.discoveredPeripherals, id: \.identifier) { peripheral in
                Button(action: {
                    bluetoothManager.connect(to: peripheral)
                    dismiss()
                }) {
                    HStack {
                        Image(systemName: "led.strip.vertical")
                            .foregroundColor(.blue)
                        VStack(alignment: .leading) {
                            Text(peripheral.name ?? "Unknown Device")
                                .font(.headline)
                            Text(peripheral.identifier.uuidString)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        Spacer()
                        Image(systemName: "chevron.right")
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("Scan for Devices")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        bluetoothManager.stopScanning()
                        dismiss()
                    }
                }
            }
            .onAppear {
                bluetoothManager.startScanning()
            }
            .onDisappear {
                bluetoothManager.stopScanning()
            }
        }
    }
}

// MARK: - Preview

struct HomeView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            HomeView(bluetoothManager: BluetoothManager())
        }
    }
}
