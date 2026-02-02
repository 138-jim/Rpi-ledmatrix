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

    var body: some View {
        List(Game.allGames) { game in
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
