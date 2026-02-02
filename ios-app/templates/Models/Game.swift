//
//  Game.swift
//  LEDMatrixController
//
//  Model representing an available game
//

import Foundation

/// Represents a playable game on the LED matrix
struct Game: Identifiable {
    let id: Int  // Index in protocol (0-4)
    let name: String
    let displayName: String
    let description: String
    let icon: String  // SF Symbol name

    /// All available games
    static let allGames: [Game] = [
        Game(
            id: 0,
            name: "snake",
            displayName: "Snake",
            description: "Classic snake game - eat, grow, avoid walls",
            icon: "snake"
        ),
        Game(
            id: 1,
            name: "pong",
            displayName: "Pong",
            description: "Retro paddle game for two players",
            icon: "rectangle.portrait.and.arrow.right"
        ),
        Game(
            id: 2,
            name: "tictactoe",
            displayName: "Tic-Tac-Toe",
            description: "Classic X's and O's strategy game",
            icon: "xmark.square"
        ),
        Game(
            id: 3,
            name: "breakout",
            displayName: "Breakout",
            description: "Break bricks with a ball and paddle",
            icon: "square.grid.3x3"
        ),
        Game(
            id: 4,
            name: "tetris",
            displayName: "Tetris",
            description: "Stack falling blocks perfectly",
            icon: "square.stack.3d.up"
        )
    ]

    /// Get game by index
    static func game(at index: Int) -> Game? {
        allGames.first { $0.id == index }
    }

    /// Get game by name
    static func game(named name: String) -> Game? {
        allGames.first { $0.name == name }
    }
}

/// Game state information
struct GameState: Codable {
    let isRunning: Bool
    let isPaused: Bool
    let gameOver: Bool
    let score: Int?

    enum CodingKeys: String, CodingKey {
        case isRunning = "running"
        case isPaused = "paused"
        case gameOver = "game_over"
        case score
    }
}
