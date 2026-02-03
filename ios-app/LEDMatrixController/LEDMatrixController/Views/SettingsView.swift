//
//  SettingsView.swift
//  LEDMatrixController
//
//  Settings and configuration view
//

import SwiftUI

struct SettingsView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @State private var powerLimit: Double = 80.0
    @State private var debounceWorkItem: DispatchWorkItem?

    var body: some View {
        Form {
            // Connection Section
            Section("Connection") {
                if bluetoothManager.isConnected {
                    HStack {
                        Image(systemName: "checkmark.circle.fill")
                            .foregroundColor(.green)
                        Text("Connected to LED Matrix")
                    }

                    Button("Disconnect", role: .destructive) {
                        bluetoothManager.disconnect()
                    }
                } else {
                    HStack {
                        Image(systemName: "exclamationmark.circle.fill")
                            .foregroundColor(.orange)
                        Text("Not connected")
                    }

                    Button("Scan for Devices") {
                        bluetoothManager.startScanning()
                    }
                }
            }

            // Power Management Section
            Section("Power Management") {
                HStack {
                    Text("Power Limit")
                    Spacer()
                    Text("\(powerLimit, specifier: "%.1f")A")
                        .foregroundColor(.secondary)
                }

                Slider(value: $powerLimit, in: 1...100, step: 0.5)
                    .onChange(of: powerLimit) { oldValue, newValue in
                        // Cancel previous debounce timer
                        debounceWorkItem?.cancel()

                        // Create new debounce timer
                        let workItem = DispatchWorkItem {
                            bluetoothManager.setPowerLimit(amps: Float(newValue))
                        }
                        debounceWorkItem = workItem

                        // Execute after 150ms delay
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.15, execute: workItem)
                    }
                    .disabled(!bluetoothManager.isConnected)

                Text("Adjust maximum current draw for LED display (1-100A)")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }

            // Display Info Section
            Section("Display Information") {
                if let config = bluetoothManager.displayConfig {
                    HStack {
                        Text("Resolution")
                        Spacer()
                        Text("\(config.grid.totalWidth)×\(config.grid.totalHeight)")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("Panels")
                        Spacer()
                        Text("\(config.panels.count)")
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("Total LEDs")
                        Spacer()
                        Text("\(config.grid.totalPixels)")
                            .foregroundColor(.secondary)
                    }
                } else {
                    Text("Connect to view display info")
                        .foregroundColor(.secondary)
                }
            }

            // Status Section
            if let status = bluetoothManager.displayStatus {
                Section("Current Status") {
                    HStack {
                        Text("FPS")
                        Spacer()
                        Text(String(format: "%.1f", status.fps))
                            .foregroundColor(.secondary)
                    }

                    HStack {
                        Text("Brightness")
                        Spacer()
                        Text("\(status.brightness)")
                            .foregroundColor(.secondary)
                    }

                    if let temp = status.temperature {
                        HStack {
                            Text("Temperature")
                            Spacer()
                            Text(String(format: "%.1f°C", temp))
                                .foregroundColor(temp > 70 ? .red : .secondary)
                        }
                    }
                }
            }

            // About Section
            Section("About") {
                HStack {
                    Text("App Version")
                    Spacer()
                    Text("1.0.0")
                        .foregroundColor(.secondary)
                }

                HStack {
                    Text("Developer")
                    Spacer()
                    Text("LED Matrix Controller")
                        .foregroundColor(.secondary)
                }
            }
        }
        .navigationTitle("Settings")
        .onAppear {
            // Sync slider with current power limit from device
            powerLimit = Double(bluetoothManager.powerLimitAmps)
        }
        .onChange(of: bluetoothManager.powerLimitAmps) { oldValue, newValue in
            // Update slider when device power limit changes
            powerLimit = Double(newValue)
        }
    }
}

// MARK: - Preview

struct SettingsView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            SettingsView(bluetoothManager: BluetoothManager())
        }
    }
}
