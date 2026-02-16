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

/// System statistics from backend
struct SystemStats: Codable {
    let cpuPercent: Double
    let cpuTempC: Double?
    let ramUsedMb: Double
    let ramTotalMb: Double
    let ramPercent: Double
    let piModel: String
    let piPowerW: Double
    let ledPowerW: Double
    let ledMaxPowerW: Double
    let totalPowerW: Double
    let ledCurrentA: Double
    let ledCount: Int

    // Power limiter stats
    struct PowerLimiterStats: Codable {
        let enabled: Bool
        let maxCurrentAmps: Double
        let wasLimited: Bool
        let currentDraw: Double
        let appliedBrightness: Int

        enum CodingKeys: String, CodingKey {
            case enabled
            case maxCurrentAmps = "max_current_amps"
            case wasLimited = "was_limited"
            case currentDraw = "current_draw"
            case appliedBrightness = "applied_brightness"
        }
    }

    let powerLimiter: PowerLimiterStats?

    enum CodingKeys: String, CodingKey {
        case cpuPercent = "cpu_percent"
        case cpuTempC = "cpu_temp_c"
        case ramUsedMb = "ram_used_mb"
        case ramTotalMb = "ram_total_mb"
        case ramPercent = "ram_percent"
        case piModel = "pi_model"
        case piPowerW = "pi_power_w"
        case ledPowerW = "led_power_w"
        case ledMaxPowerW = "led_max_power_w"
        case totalPowerW = "total_power_w"
        case ledCurrentA = "led_current_a"
        case ledCount = "led_count"
        case powerLimiter = "power_limiter"
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
