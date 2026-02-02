//
//  GameControllerView.swift
//  LEDMatrixController
//
//  Virtual D-pad controller for games
//

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
            .padding()
        }
        .padding()
    }
}

// MARK: - Game Button Component

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
                .shadow(radius: 5)
        }
    }
}

// MARK: - Preview

struct GameControllerView_Previews: PreviewProvider {
    static var previews: some View {
        GameControllerView(bluetoothManager: BluetoothManager())
    }
}
