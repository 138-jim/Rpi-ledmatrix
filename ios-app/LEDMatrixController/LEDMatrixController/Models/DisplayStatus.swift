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
    var enabled: Bool
    var offTime: Date      // Store as Date for DatePicker compatibility
    var onTime: Date       // Store as Date for DatePicker compatibility
    var isSleeping: Bool   // Read-only status from backend

    // Helper computed properties to extract hour/minute components
    var offHour: UInt8 {
        UInt8(Calendar.current.component(.hour, from: offTime))
    }

    var offMinute: UInt8 {
        UInt8(Calendar.current.component(.minute, from: offTime))
    }

    var onHour: UInt8 {
        UInt8(Calendar.current.component(.hour, from: onTime))
    }

    var onMinute: UInt8 {
        UInt8(Calendar.current.component(.minute, from: onTime))
    }

    /// Default schedule: Off at 11pm, on at 7am, disabled
    static var defaultSchedule: SleepSchedule {
        let calendar = Calendar.current
        let offTime = calendar.date(from: DateComponents(hour: 23, minute: 0)) ?? Date()
        let onTime = calendar.date(from: DateComponents(hour: 7, minute: 0)) ?? Date()

        return SleepSchedule(
            enabled: false,
            offTime: offTime,
            onTime: onTime,
            isSleeping: false
        )
    }
}
