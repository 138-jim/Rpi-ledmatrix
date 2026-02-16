//
//  SystemMonitorView.swift
//  LEDMatrixController
//
//  System statistics and monitoring dashboard
//

import SwiftUI
import Combine

struct SystemMonitorView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @State private var systemStats: SystemStats?
    @State private var isRefreshing = false
    @State private var autoRefresh = true
    @State private var errorMessage: String?

    // Auto-refresh timer
    let timer = Timer.publish(every: 2, on: .main, in: .common).autoconnect()

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header
                HStack {
                    VStack(alignment: .leading) {
                        Text("System Monitor")
                            .font(.title2)
                            .bold()

                        if let stats = systemStats {
                            Text(stats.piModel)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                    }

                    Spacer()

                    // Auto-refresh toggle
                    Toggle("Auto", isOn: $autoRefresh)
                        .labelsHidden()
                        .onChange(of: autoRefresh) { _, newValue in
                            if newValue {
                                fetchStats()
                            }
                        }

                    // Manual refresh button
                    Button(action: { fetchStats() }) {
                        Image(systemName: "arrow.clockwise")
                            .rotationEffect(.degrees(isRefreshing ? 360 : 0))
                    }
                    .disabled(isRefreshing || !bluetoothManager.isConnected)
                }
                .padding()

                if !bluetoothManager.isConnected {
                    // Not connected message
                    VStack(spacing: 12) {
                        Image(systemName: "wifi.slash")
                            .font(.system(size: 48))
                            .foregroundColor(.red)

                        Text("Connect to display to view system stats")
                            .font(.headline)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                } else if let error = errorMessage {
                    // Error message
                    VStack(spacing: 12) {
                        Image(systemName: "exclamationmark.triangle")
                            .font(.system(size: 48))
                            .foregroundColor(.orange)

                        Text(error)
                            .font(.caption)
                            .foregroundColor(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                } else if let stats = systemStats {
                    // Stats display
                    VStack(spacing: 16) {
                        // CPU Section
                        StatSection(title: "CPU", icon: "cpu") {
                            StatRow(label: "Usage", value: "\(Int(stats.cpuPercent))%", color: cpuColor(stats.cpuPercent))

                            if let temp = stats.cpuTempC {
                                StatRow(label: "Temperature", value: String(format: "%.1f°C", temp), color: tempColor(temp))
                            }
                        }

                        // Memory Section
                        StatSection(title: "Memory", icon: "memorychip") {
                            StatRow(label: "Used", value: String(format: "%.0f MB", stats.ramUsedMb))
                            StatRow(label: "Total", value: String(format: "%.0f MB", stats.ramTotalMb))
                            ProgressView(value: stats.ramPercent / 100.0)
                                .tint(ramColor(stats.ramPercent))
                            Text("\(Int(stats.ramPercent))%")
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }

                        // Power Section
                        StatSection(title: "Power Consumption", icon: "bolt.fill") {
                            StatRow(label: "Raspberry Pi", value: String(format: "%.1f W", stats.piPowerW))
                            StatRow(label: "LED Display", value: String(format: "%.1f W", stats.ledPowerW), color: .orange)
                            StatRow(label: "Total Power", value: String(format: "%.1f W", stats.totalPowerW), color: .blue)

                            Divider()

                            StatRow(label: "Current Draw", value: String(format: "%.2f A", stats.ledCurrentA))
                            StatRow(label: "LED Count", value: "\(stats.ledCount) pixels")
                        }

                        // Power Limiter Section
                        if let limiter = stats.powerLimiter {
                            StatSection(
                                title: "Power Limiter",
                                icon: limiter.wasLimited ? "exclamationmark.triangle.fill" : "checkmark.shield.fill"
                            ) {
                                HStack {
                                    Text("Status")
                                    Spacer()
                                    Text(limiter.enabled ? "Enabled" : "Disabled")
                                        .foregroundColor(limiter.enabled ? .green : .secondary)
                                }

                                if limiter.enabled {
                                    StatRow(label: "Limit", value: String(format: "%.1f A", limiter.maxCurrentAmps))
                                    StatRow(
                                        label: "Current Draw",
                                        value: String(format: "%.2f A", limiter.currentDraw),
                                        color: limiter.wasLimited ? .orange : .primary
                                    )

                                    if limiter.wasLimited {
                                        HStack {
                                            Image(systemName: "exclamationmark.triangle.fill")
                                                .foregroundColor(.orange)
                                            Text("Brightness reduced to \(limiter.appliedBrightness)")
                                                .font(.caption)
                                                .foregroundColor(.orange)
                                        }
                                    }
                                }
                            }
                        }
                    }
                    .padding(.horizontal)
                } else {
                    // Loading state
                    ProgressView("Loading stats...")
                        .padding()
                }

                Spacer()
            }
        }
        .navigationTitle("System Monitor")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            if bluetoothManager.isConnected {
                fetchStats()
            }
        }
        .onReceive(timer) { _ in
            if autoRefresh && bluetoothManager.isConnected && !isRefreshing {
                fetchStats()
            }
        }
    }

    private func fetchStats() {
        guard bluetoothManager.isConnected else { return }

        isRefreshing = true
        errorMessage = nil

        APIClient.shared.fetchSystemStats { result in
            // APIClient already dispatches to main thread
            self.isRefreshing = false

            switch result {
            case .success(let stats):
                self.systemStats = stats
                self.errorMessage = nil
            case .failure(let error):
                self.errorMessage = error.localizedDescription
                print("❌ System stats fetch error: \(error.localizedDescription)")
            }
        }
    }

    // Color helpers
    private func cpuColor(_ percent: Double) -> Color {
        if percent > 80 { return .red }
        if percent > 60 { return .orange }
        return .green
    }

    private func tempColor(_ celsius: Double) -> Color {
        if celsius > 80 { return .red }
        if celsius > 70 { return .orange }
        return .green
    }

    private func ramColor(_ percent: Double) -> Color {
        if percent > 85 { return .red }
        if percent > 70 { return .orange }
        return .green
    }
}

// MARK: - Stat Section Component

struct StatSection<Content: View>: View {
    let title: String
    let icon: String
    @ViewBuilder let content: Content

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: icon)
                    .foregroundColor(.blue)
                Text(title)
                    .font(.headline)
            }

            VStack(spacing: 8) {
                content
            }
            .padding()
            .background(Color(.systemGray6))
            .cornerRadius(10)
        }
    }
}

// MARK: - Stat Row Component

struct StatRow: View {
    let label: String
    let value: String
    var color: Color = .primary

    var body: some View {
        HStack {
            Text(label)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .bold()
                .foregroundColor(color)
        }
        .font(.system(.body, design: .monospaced))
    }
}

// MARK: - Preview

struct SystemMonitorView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            SystemMonitorView(bluetoothManager: BluetoothManager())
        }
    }
}
