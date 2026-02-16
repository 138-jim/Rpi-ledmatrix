//
//  PanelConfigView.swift
//  LEDMatrixController
//
//  Panel configuration and layout tool
//

import SwiftUI

struct PanelConfigView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @State private var selectedPanelId: Int?
    @State private var showingRotationPicker = false

    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Header info
                if let config = bluetoothManager.displayConfig {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Display Configuration")
                            .font(.title2)
                            .bold()

                        HStack {
                            Label("\(config.grid.totalWidth)×\(config.grid.totalHeight) pixels", systemImage: "grid")
                            Spacer()
                            Label("\(config.panels.count) panels", systemImage: "square.grid.2x2")
                        }
                        .font(.caption)
                        .foregroundColor(.secondary)
                    }
                    .padding()

                    // Visual panel grid
                    PanelGridView(
                        config: config,
                        selectedPanelId: $selectedPanelId
                    )
                    .padding()

                    // Panel list
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Panel Details")
                            .font(.headline)
                            .padding(.horizontal)

                        ForEach(config.panels) { panel in
                            PanelDetailRow(
                                panel: panel,
                                isSelected: selectedPanelId == panel.id,
                                onSelect: { selectedPanelId = panel.id },
                                onRotate: { newRotation in
                                    updatePanelRotation(panelId: panel.id, rotation: newRotation)
                                }
                            )
                        }
                    }

                    // Grid settings
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Grid Settings")
                            .font(.headline)
                            .padding(.horizontal)

                        VStack(spacing: 0) {
                            SettingRow(label: "Grid Size", value: "\(config.grid.gridWidth)×\(config.grid.gridHeight) panels")
                            Divider()
                            SettingRow(label: "Panel Size", value: "\(config.grid.panelWidth)×\(config.grid.panelHeight) LEDs")
                            Divider()
                            SettingRow(label: "Wiring Pattern", value: config.grid.wiringPattern)
                        }
                        .background(Color(.systemGray6))
                        .cornerRadius(10)
                        .padding(.horizontal)
                    }
                    .padding(.top)

                } else if bluetoothManager.isConnected {
                    ProgressView("Loading configuration...")
                        .padding()
                } else {
                    VStack(spacing: 12) {
                        Image(systemName: "square.grid.2x2.slash")
                            .font(.system(size: 48))
                            .foregroundColor(.secondary)

                        Text("Connect to display to view panel configuration")
                            .font(.headline)
                            .multilineTextAlignment(.center)
                    }
                    .padding()
                }

                Spacer()
            }
        }
        .navigationTitle("Panel Config")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func updatePanelRotation(panelId: Int, rotation: Int) {
        // TODO: Implement panel rotation update via API
        print("🔄 Update panel \(panelId) rotation to \(rotation)°")
        // Would need HTTP API call to update configuration
    }
}

// MARK: - Panel Grid Visualization

struct PanelGridView: View {
    let config: LEDDisplayConfig
    @Binding var selectedPanelId: Int?

    var body: some View {
        GeometryReader { geometry in
            let gridWidth = config.grid.gridWidth
            let gridHeight = config.grid.gridHeight
            let cellSize = min(geometry.size.width / CGFloat(gridWidth),
                             geometry.size.height / CGFloat(gridHeight))

            VStack(spacing: 2) {
                ForEach(0..<gridHeight, id: \.self) { row in
                    HStack(spacing: 2) {
                        ForEach(0..<gridWidth, id: \.self) { col in
                            if let panel = findPanel(at: row, col: col) {
                                PanelCell(
                                    panel: panel,
                                    isSelected: selectedPanelId == panel.id,
                                    size: cellSize
                                )
                                .onTapGesture {
                                    selectedPanelId = panel.id
                                }
                            } else {
                                // Empty cell
                                Rectangle()
                                    .fill(Color(.systemGray5))
                                    .frame(width: cellSize, height: cellSize)
                                    .cornerRadius(8)
                            }
                        }
                    }
                }
            }
            .frame(width: CGFloat(gridWidth) * (cellSize + 2),
                   height: CGFloat(gridHeight) * (cellSize + 2))
            .position(x: geometry.size.width / 2, y: geometry.size.height / 2)
        }
        .aspectRatio(CGFloat(config.grid.gridWidth) / CGFloat(config.grid.gridHeight), contentMode: .fit)
    }

    private func findPanel(at row: Int, col: Int) -> Panel? {
        config.panels.first { panel in
            panel.position[0] == col && panel.position[1] == row
        }
    }
}

// MARK: - Panel Cell

struct PanelCell: View {
    let panel: Panel
    let isSelected: Bool
    let size: CGFloat

    var body: some View {
        ZStack {
            RoundedRectangle(cornerRadius: 8)
                .fill(isSelected ? Color.blue.opacity(0.3) : Color(.systemGray6))
                .overlay(
                    RoundedRectangle(cornerRadius: 8)
                        .stroke(isSelected ? Color.blue : Color.clear, lineWidth: 3)
                )

            VStack(spacing: 4) {
                Text("Panel \(panel.id)")
                    .font(.caption)
                    .bold()

                Image(systemName: rotationIcon(panel.rotation))
                    .font(.title2)
                    .foregroundColor(.blue)

                Text("\(panel.rotation)°")
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }
        }
        .frame(width: size, height: size)
    }

    private func rotationIcon(_ degrees: Int) -> String {
        switch degrees {
        case 0: return "arrow.up.circle.fill"
        case 90: return "arrow.right.circle.fill"
        case 180: return "arrow.down.circle.fill"
        case 270: return "arrow.left.circle.fill"
        default: return "arrow.clockwise.circle.fill"
        }
    }
}

// MARK: - Panel Detail Row

struct PanelDetailRow: View {
    let panel: Panel
    let isSelected: Bool
    let onSelect: () -> Void
    let onRotate: (Int) -> Void

    @State private var showingRotationPicker = false

    var body: some View {
        VStack(spacing: 0) {
            Button(action: onSelect) {
                HStack {
                    // Panel indicator
                    Circle()
                        .fill(isSelected ? Color.blue : Color(.systemGray4))
                        .frame(width: 12, height: 12)

                    Text("Panel \(panel.id)")
                        .font(.headline)
                        .foregroundColor(.primary)

                    Spacer()

                    // Position
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("Position")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        Text("(\(panel.position[0]), \(panel.position[1]))")
                            .font(.caption)
                            .foregroundColor(.primary)
                    }

                    // Rotation
                    VStack(alignment: .trailing, spacing: 2) {
                        Text("Rotation")
                            .font(.caption2)
                            .foregroundColor(.secondary)
                        Text("\(panel.rotation)°")
                            .font(.caption)
                            .foregroundColor(.primary)
                    }
                    .padding(.leading, 12)

                    Image(systemName: rotationIcon(panel.rotation))
                        .foregroundColor(.blue)
                        .padding(.leading, 8)
                }
                .padding()
                .background(isSelected ? Color.blue.opacity(0.1) : Color(.systemGray6))
                .cornerRadius(10)
            }
            .buttonStyle(PlainButtonStyle())

            // Rotation controls (shown when selected)
            if isSelected {
                HStack(spacing: 12) {
                    Text("Rotate:")
                        .font(.caption)
                        .foregroundColor(.secondary)

                    ForEach([0, 90, 180, 270], id: \.self) { rotation in
                        Button(action: { onRotate(rotation) }) {
                            VStack(spacing: 4) {
                                Image(systemName: rotationIcon(rotation))
                                    .font(.title3)
                                Text("\(rotation)°")
                                    .font(.caption2)
                            }
                            .foregroundColor(panel.rotation == rotation ? .white : .blue)
                            .padding(8)
                            .background(panel.rotation == rotation ? Color.blue : Color.clear)
                            .cornerRadius(8)
                            .overlay(
                                RoundedRectangle(cornerRadius: 8)
                                    .stroke(Color.blue, lineWidth: 1)
                            )
                        }
                    }

                    Spacer()
                }
                .padding()
                .background(Color(.systemGray5))
            }
        }
        .padding(.horizontal)
    }

    private func rotationIcon(_ degrees: Int) -> String {
        switch degrees {
        case 0: return "arrow.up"
        case 90: return "arrow.right"
        case 180: return "arrow.down"
        case 270: return "arrow.left"
        default: return "arrow.clockwise"
        }
    }
}

// MARK: - Setting Row

struct SettingRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            Text(label)
                .foregroundColor(.secondary)
            Spacer()
            Text(value)
                .bold()
        }
        .padding()
    }
}

// MARK: - Preview

struct PanelConfigView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            PanelConfigView(bluetoothManager: BluetoothManager())
        }
    }
}
