//
//  DisplayStatus.swift
//  LEDMatrixController
//
//  Model for LED display status information
//

import Foundation

/// Real-time status of the LED display
struct DisplayStatus: Codable {
    let fps: Float
    let brightness: UInt8
    let width: Int
    let height: Int
    let ledCount: Int
    let queueSize: Int
    let temperature: Float?
    let powerDraw: Float?

    enum CodingKeys: String, CodingKey {
        case fps
        case brightness
        case width
        case height
        case ledCount = "led_count"
        case queueSize = "queue_size"
        case temperature
        case powerDraw = "power_draw"
    }

    /// Default/placeholder status
    static let placeholder = DisplayStatus(
        fps: 0,
        brightness: 128,
        width: 32,
        height: 32,
        ledCount: 1024,
        queueSize: 0,
        temperature: nil,
        powerDraw: nil
    )
}

/// Power limit configuration
struct PowerLimit: Codable {
    let maxCurrentAmps: Float
    let enabled: Bool

    enum CodingKeys: String, CodingKey {
        case maxCurrentAmps = "max_current_amps"
        case enabled
    }
}

/// Sleep schedule configuration
struct SleepSchedule: Codable {
    let offTime: String  // "HH:MM" format
    let onTime: String   // "HH:MM" format
    let enabled: Bool

    enum CodingKeys: String, CodingKey {
        case offTime = "off_time"
        case onTime = "on_time"
        case enabled
    }
}
