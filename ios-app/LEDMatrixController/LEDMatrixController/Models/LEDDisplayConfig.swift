//
//  LEDDisplayConfig.swift
//  LEDMatrixController
//
//  Model for LED display configuration
//

import Foundation

/// Complete LED display configuration
struct LEDDisplayConfig: Codable {
    let grid: GridConfig
    let panels: [Panel]
}

/// Grid configuration defining display layout
struct GridConfig: Codable {
    let gridWidth: Int
    let gridHeight: Int
    let panelWidth: Int
    let panelHeight: Int
    let wiringPattern: String

    enum CodingKeys: String, CodingKey {
        case gridWidth = "grid_width"
        case gridHeight = "grid_height"
        case panelWidth = "panel_width"
        case panelHeight = "panel_height"
        case wiringPattern = "wiring_pattern"
    }

    /// Total display dimensions in pixels
    var totalWidth: Int {
        gridWidth * panelWidth
    }

    var totalHeight: Int {
        gridHeight * panelHeight
    }

    var totalPixels: Int {
        totalWidth * totalHeight
    }
}

/// Individual panel configuration
struct Panel: Codable {
    let id: Int
    let rotation: Int  // 0, 90, 180, or 270 degrees
    let position: [Int]  // [x, y] in grid coordinates
}
