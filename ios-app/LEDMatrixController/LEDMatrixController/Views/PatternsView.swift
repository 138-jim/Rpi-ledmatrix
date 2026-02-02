//
//  PatternsView.swift
//  LEDMatrixController
//
//  View for selecting and displaying LED patterns
//

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
                                    .lineLimit(1)
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
