//
//  DisplayPattern.swift
//  LEDMatrixController
//
//  Model representing an LED matrix display pattern
//

import Foundation

/// Category for organizing patterns in the UI
enum PatternCategory: String, CaseIterable {
    case solid = "Solid Colors"
    case geometric = "Geometric"
    case animated = "Animated Effects"
    case gradients = "Gradients & Colors"
    case natural = "Natural Phenomena"
    case complex = "Complex Animations"
    case timeBased = "Time-Based"
}

/// Represents a displayable pattern
struct DisplayPattern: Identifiable {
    let id: Int  // Index in protocol
    let name: String
    let category: PatternCategory
    let description: String

    /// Get pattern by index
    static func pattern(at index: Int) -> DisplayPattern? {
        guard index >= 0 && index < allPatterns.count else { return nil }
        return allPatterns[index]
    }

    /// Get pattern by name
    static func pattern(named name: String) -> DisplayPattern? {
        allPatterns.first { $0.name == name }
    }

    /// All available patterns organized by category
    static let allPatterns: [DisplayPattern] = [
        // Solid Colors (0-3)
        DisplayPattern(id: 0, name: "red", category: .solid, description: "Solid red color"),
        DisplayPattern(id: 1, name: "green", category: .solid, description: "Solid green color"),
        DisplayPattern(id: 2, name: "blue", category: .solid, description: "Solid blue color"),
        DisplayPattern(id: 3, name: "white", category: .solid, description: "Solid white color"),

        // Geometric (4-8)
        DisplayPattern(id: 4, name: "corners", category: .geometric, description: "Corner markers for alignment"),
        DisplayPattern(id: 5, name: "cross", category: .geometric, description: "Crosshair pattern"),
        DisplayPattern(id: 6, name: "checkerboard", category: .geometric, description: "Classic checkerboard"),
        DisplayPattern(id: 7, name: "grid", category: .geometric, description: "Grid pattern"),
        DisplayPattern(id: 8, name: "panels", category: .geometric, description: "Shows panel numbers"),

        // Animated Effects (9-13)
        DisplayPattern(id: 9, name: "spiral", category: .animated, description: "Spiral rainbow animation"),
        DisplayPattern(id: 10, name: "wave", category: .animated, description: "Wave pattern animation"),
        DisplayPattern(id: 11, name: "fire", category: .animated, description: "Fire effect simulation"),
        DisplayPattern(id: 12, name: "plasma", category: .animated, description: "Plasma effect"),
        DisplayPattern(id: 13, name: "geometric_patterns", category: .animated, description: "Animated geometric shapes"),

        // Gradients & Colors (14-17)
        DisplayPattern(id: 14, name: "rainbow", category: .gradients, description: "Rainbow gradient"),
        DisplayPattern(id: 15, name: "color_gradients", category: .gradients, description: "Color gradient transitions"),
        DisplayPattern(id: 16, name: "gradient_waves", category: .gradients, description: "Waving gradients"),
        DisplayPattern(id: 17, name: "rgb_torch", category: .gradients, description: "RGB torch effect"),

        // Natural Phenomena (18-26)
        DisplayPattern(id: 18, name: "snow", category: .natural, description: "Falling snow"),
        DisplayPattern(id: 19, name: "rain", category: .natural, description: "Falling rain"),
        DisplayPattern(id: 20, name: "fireflies", category: .natural, description: "Twinkling fireflies"),
        DisplayPattern(id: 21, name: "aquarium", category: .natural, description: "Bubbling aquarium"),
        DisplayPattern(id: 22, name: "ocean_waves", category: .natural, description: "Ocean waves"),
        DisplayPattern(id: 23, name: "northern_lights", category: .natural, description: "Aurora borealis"),
        DisplayPattern(id: 24, name: "starfield", category: .natural, description: "Starfield animation"),
        DisplayPattern(id: 25, name: "starry_night", category: .natural, description: "Starry night sky"),
        DisplayPattern(id: 26, name: "fireworks", category: .natural, description: "Fireworks display"),

        // Complex Animations (27-32)
        DisplayPattern(id: 27, name: "heart", category: .complex, description: "Beating heart"),
        DisplayPattern(id: 28, name: "dna_helix", category: .complex, description: "DNA helix animation"),
        DisplayPattern(id: 29, name: "kaleidoscope", category: .complex, description: "Kaleidoscope effect"),
        DisplayPattern(id: 30, name: "perlin_noise_flow", category: .complex, description: "Perlin noise flow"),
        DisplayPattern(id: 31, name: "matrix_rain", category: .complex, description: "Matrix-style digital rain"),
        DisplayPattern(id: 32, name: "lava_lamp", category: .complex, description: "Lava lamp effect"),

        // Time-based (33-36)
        DisplayPattern(id: 33, name: "elapsed", category: .timeBased, description: "Elapsed time display"),
        DisplayPattern(id: 34, name: "sunset_sunrise", category: .timeBased, description: "Sunset/sunrise cycle"),
        DisplayPattern(id: 35, name: "sunset_sunrise_loop", category: .timeBased, description: "Looping sunset/sunrise"),
        DisplayPattern(id: 36, name: "dot", category: .timeBased, description: "Moving dot")
    ]

    /// Patterns grouped by category
    static var categorized: [PatternCategory: [DisplayPattern]] {
        Dictionary(grouping: allPatterns, by: { $0.category })
    }

    /// Create dynamic patterns from device pattern list
    static func createDynamicPatterns(from patternNames: [String]) -> [DisplayPattern] {
        patternNames.enumerated().map { index, name in
            // Try to match with existing pattern for category and description
            if let existing = allPatterns.first(where: { $0.name == name }) {
                return existing
            } else {
                // Create new pattern with generic category
                return DisplayPattern(
                    id: index,
                    name: name,
                    category: .animated,  // Default category for unknown patterns
                    description: name.replacingOccurrences(of: "_", with: " ").capitalized
                )
            }
        }
    }

    /// Create categorized dictionary from dynamic patterns
    static func categorizeDynamic(_ patterns: [DisplayPattern]) -> [PatternCategory: [DisplayPattern]] {
        Dictionary(grouping: patterns, by: { $0.category })
    }
}
