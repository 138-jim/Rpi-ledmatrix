//
//  GamesView.swift
//  LEDMatrixController
//
//  View for selecting and starting games
//

import SwiftUI

struct GamesView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @State private var showingGameController = false

    // Compute games to display (dynamic if available, otherwise static)
    private var displayGames: [Game] {
        if !bluetoothManager.availableGames.isEmpty {
            return Game.createDynamicGames(from: bluetoothManager.availableGames)
        } else {
            return Game.allGames
        }
    }

    var body: some View {
        List {
            // Show source indicator
            Section {
                HStack {
                    Image(systemName: bluetoothManager.availableGames.isEmpty ? "laptopcomputer" : "antenna.radiowaves.left.and.right")
                        .foregroundColor(bluetoothManager.availableGames.isEmpty ? .orange : .green)
                    Text(bluetoothManager.availableGames.isEmpty ? "Using built-in game list" : "Loaded \(bluetoothManager.availableGames.count) games from device")
                        .font(.caption)
                        .foregroundColor(.secondary)
                    Spacer()
                    if bluetoothManager.isConnected && bluetoothManager.availableGames.isEmpty {
                        Button("Refresh") {
                            bluetoothManager.requestGameList()
                        }
                        .font(.caption)
                    }
                }
            }

            // Display games
            Section {
                ForEach(displayGames) { game in
                    Button(action: {
                        bluetoothManager.startGame(UInt8(game.id))
                        showingGameController = true
                    }) {
                        HStack {
                            Image(systemName: game.icon)
                                .font(.largeTitle)
                                .foregroundColor(.blue)
                                .frame(width: 60)

                            VStack(alignment: .leading) {
                                Text(game.displayName)
                                    .font(.headline)
                                Text(game.description)
                                    .font(.caption)
                                    .foregroundColor(.secondary)
                            }

                            Spacer()

                            Image(systemName: "play.circle.fill")
                                .foregroundColor(.green)
                        }
                    }
                }
            }
        }
        .navigationTitle("Games")
        .disabled(!bluetoothManager.isConnected)
        .sheet(isPresented: $showingGameController) {
            GameControllerView(bluetoothManager: bluetoothManager)
        }
    }
}

// MARK: - Preview

struct GamesView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            GamesView(bluetoothManager: BluetoothManager())
        }
    }
}
