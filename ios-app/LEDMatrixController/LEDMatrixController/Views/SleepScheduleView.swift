//
//  SleepScheduleView.swift
//  LEDMatrixController
//
//  Sleep schedule settings component
//

import SwiftUI

struct SleepScheduleSettingsSection: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @State private var localSchedule: SleepSchedule
    @State private var debounceWorkItem: DispatchWorkItem?
    @Environment(\.scenePhase) var scenePhase

    init(bluetoothManager: BluetoothManager) {
        self.bluetoothManager = bluetoothManager
        self._localSchedule = State(initialValue: bluetoothManager.sleepSchedule)
    }

    var body: some View {
        Section("Sleep Schedule") {
            Toggle("Enable Auto Sleep", isOn: $localSchedule.enabled)
                .onChange(of: localSchedule.enabled) { oldValue, newValue in
                    sendScheduleUpdate()
                }
                .disabled(!bluetoothManager.isConnected)

            if localSchedule.enabled {
                // Off Time Picker
                DatePicker(
                    "Sleep At",
                    selection: $localSchedule.offTime,
                    displayedComponents: .hourAndMinute
                )
                .onChange(of: localSchedule.offTime) { oldValue, newValue in
                    sendScheduleUpdate()
                }
                .disabled(!bluetoothManager.isConnected)

                // On Time Picker
                DatePicker(
                    "Wake At",
                    selection: $localSchedule.onTime,
                    displayedComponents: .hourAndMinute
                )
                .onChange(of: localSchedule.onTime) { oldValue, newValue in
                    sendScheduleUpdate()
                }
                .disabled(!bluetoothManager.isConnected)

                // Current status
                if localSchedule.isSleeping {
                    HStack {
                        Image(systemName: "moon.fill")
                            .foregroundColor(.blue)
                        Text("Display is currently sleeping")
                            .font(.caption)
                            .foregroundColor(.secondary)
                    }
                }

                // Help text
                Text("Display will automatically turn off and on at scheduled times")
                    .font(.caption)
                    .foregroundColor(.secondary)
            }
        }
        .onChange(of: scenePhase) { oldPhase, newPhase in
            // Flush pending updates when app backgrounds
            if newPhase == .background {
                debounceWorkItem?.cancel()
                sendScheduleUpdateImmediately()
            }
        }
    }

    private func sendScheduleUpdate() {
        // Cancel previous debounce timer
        debounceWorkItem?.cancel()

        // Create new debounce timer (1 second delay to avoid rapid updates while adjusting time)
        let workItem = DispatchWorkItem { [self] in
            sendScheduleUpdateImmediately()
        }
        debounceWorkItem = workItem

        // Execute after delay
        DispatchQueue.main.asyncAfter(deadline: .now() + 1.0, execute: workItem)
    }

    private func sendScheduleUpdateImmediately() {
        bluetoothManager.setSleepSchedule(
            offHour: localSchedule.offHour,
            offMin: localSchedule.offMinute,
            onHour: localSchedule.onHour,
            onMin: localSchedule.onMinute,
            enabled: localSchedule.enabled
        )
    }
}
