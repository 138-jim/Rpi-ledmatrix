//
//  PatternsView.swift
//  LEDMatrixController
//
//  View for selecting and displaying LED patterns
//

import SwiftUI

struct PatternsView: View {
    @ObservedObject var bluetoothManager: BluetoothManager

    // Compute patterns to display (dynamic if available, otherwise static)
    private var displayPatterns: [DisplayPattern] {
        if !bluetoothManager.availablePatterns.isEmpty {
            return DisplayPattern.createDynamicPatterns(from: bluetoothManager.availablePatterns)
        } else {
            return DisplayPattern.allPatterns
        }
    }

    private var categorizedPatterns: [PatternCategory: [DisplayPattern]] {
        DisplayPattern.categorizeDynamic(displayPatterns)
    }

    var body: some View {
        List {
            // Show source indicator
            Section {
                HStack {
                    Image(systemName: bluetoothManager.availablePatterns.isEmpty ? "laptopcomputer" : "antenna.radiowaves.left.and.right")
                        .foregroundColor(bluetoothManager.availablePatterns.isEmpty ? .orange : .green)
                    Text(bluetoothManager.availablePatterns.isEmpty ? "Using built-in pattern list" : "Loaded \(bluetoothManager.availablePatterns.count) patterns from device")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    if bluetoothManager.isConnected && bluetoothManager.availablePatterns.isEmpty {
                        Button("Refresh") {
                            bluetoothManager.requestPatternList()
                        }
                        .font(.caption)
                    }
                }
            }

            // Display patterns by category
            ForEach(PatternCategory.allCases, id: \.self) { category in
                if let patterns = categorizedPatterns[category], !patterns.isEmpty {
                    Section(header: Text(category.rawValue)) {
                        ForEach(patterns, id: \.id) { pattern in
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
                                        .lineLimit(1)
                                }
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

// MARK: - Preview

struct PatternsView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            PatternsView(bluetoothManager: BluetoothManager())
        }
    }
}
