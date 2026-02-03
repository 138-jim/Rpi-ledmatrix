//
//  Protocol.swift
//  LEDMatrixController
//
//  BLE Protocol constants matching the Raspberry Pi bridge service
//

import Foundation
import CoreBluetooth

/// BLE Protocol constants for LED Matrix communication
struct BLEProtocol {

    // MARK: - Service and Characteristic UUIDs

    static let serviceUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef0")

    static let brightnessUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef1")
    static let patternUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef2")
    static let gameControlUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef3")
    static let statusUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef4")
    static let configUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef5")
    static let powerLimitUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef6")
    static let sleepScheduleUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef7")
    static let frameStreamUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef8")
    static let patternListUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdef9")
    static let gameListUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdefa")
    static let capabilitiesUUID = CBUUID(string: "12345678-1234-5678-1234-56789abcdeff")

    // MARK: - Pattern Names (indices 0-36)

    static let patterns: [String] = [
        // Solid Colors (0-3)
        "red", "green", "blue", "white",

        // Geometric (4-8)
        "corners", "cross", "checkerboard", "grid", "panels",

        // Animated Effects (9-13)
        "spiral", "wave", "fire", "plasma", "geometric_patterns",

        // Gradients & Colors (14-17)
        "rainbow", "color_gradients", "gradient_waves", "rgb_torch",

        // Natural Phenomena (18-26)
        "snow", "rain", "fireflies", "aquarium", "ocean_waves",
        "northern_lights", "starfield", "starry_night", "fireworks",

        // Complex Animations (27-32)
        "heart", "dna_helix", "kaleidoscope", "perlin_noise_flow",
        "matrix_rain", "lava_lamp",

        // Time-based (33-36)
        "elapsed", "sunset_sunrise", "sunset_sunrise_loop", "dot"
    ]

    // MARK: - Game Names (indices 0-4)

    static let games: [String] = [
        "snake",
        "pong",
        "tictactoe",
        "breakout",
        "tetris"
    ]

    // MARK: - Constants

    static let maxChunkSize = 500  // Maximum bytes per BLE write
    static let deviceName = "LED Matrix"  // BLE peripheral name to scan for
}

/// Game actions matching the bridge protocol
enum GameAction: UInt8 {
    case up = 0
    case down = 1
    case left = 2
    case right = 3
    case action = 4  // Select, fire, etc.
    case reset = 5
    case pause = 6
    case resume = 7
}

/// Pattern list response from device
struct PatternListResponse: Codable {
    let patterns: [String]
    let count: Int
}

/// Game list response from device
struct GameListResponse: Codable {
    let games: [String]
    let count: Int
}

/// Device capabilities response
struct DeviceCapabilities: Codable {
    let hasGames: Bool
    let hasPatterns: Bool
    let hasFrameStreaming: Bool
    let hasPowerLimiter: Bool
    let hasSleepScheduler: Bool
    let hasBrightnessControl: Bool
    let firmwareVersion: String

    enum CodingKeys: String, CodingKey {
        case hasGames = "has_games"
        case hasPatterns = "has_patterns"
        case hasFrameStreaming = "has_frame_streaming"
        case hasPowerLimiter = "has_power_limiter"
        case hasSleepScheduler = "has_sleep_scheduler"
        case hasBrightnessControl = "has_brightness_control"
        case firmwareVersion = "firmware_version"
    }
}
