//
//  Item.swift
//  LEDMatrixController
//
//  Created by Jim on 3/2/2026.
//

import Foundation
import SwiftData

@Model
final class Item {
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
