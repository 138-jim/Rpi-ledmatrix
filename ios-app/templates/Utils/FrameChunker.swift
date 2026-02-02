//
//  FrameChunker.swift
//  LEDMatrixController
//
//  Utility for chunking large frames for BLE transmission
//

import Foundation

/// Handles splitting frames into BLE-compatible chunks
struct FrameChunker {

    /// Maximum data size per BLE write
    static let maxChunkSize = 500

    /// Split RGB frame data into chunks for BLE transmission
    /// - Parameters:
    ///   - rgbData: Raw RGB data (width × height × 3 bytes)
    ///   - width: Frame width in pixels
    ///   - height: Frame height in pixels
    /// - Returns: Array of Data chunks ready for BLE transmission
    static func chunkFrame(_ rgbData: Data, width: Int, height: Int) -> [Data] {
        var chunks: [Data] = []
        var sequenceNum: UInt16 = 0
        var offset = 0

        // First chunk includes header (sequence + width + height)
        var firstChunk = Data()

        // Sequence number (2 bytes, big-endian)
        firstChunk.append(contentsOf: withUnsafeBytes(of: sequenceNum.bigEndian) { Array($0) })

        // Width (2 bytes, big-endian)
        let widthBytes = UInt16(width).bigEndian
        firstChunk.append(contentsOf: withUnsafeBytes(of: widthBytes) { Array($0) })

        // Height (2 bytes, big-endian)
        let heightBytes = UInt16(height).bigEndian
        firstChunk.append(contentsOf: withUnsafeBytes(of: heightBytes) { Array($0) })

        // Add as much data as fits in first chunk
        let firstChunkDataSize = maxChunkSize - 6  // 2 (seq) + 4 (header)
        let firstData = rgbData.prefix(firstChunkDataSize)
        firstChunk.append(firstData)
        chunks.append(firstChunk)

        offset = firstChunkDataSize
        sequenceNum += 1

        // Remaining chunks
        while offset < rgbData.count {
            var chunk = Data()

            // Sequence number (2 bytes, big-endian)
            chunk.append(contentsOf: withUnsafeBytes(of: sequenceNum.bigEndian) { Array($0) })

            // Add data
            let chunkDataSize = min(maxChunkSize - 2, rgbData.count - offset)
            let chunkData = rgbData.subdata(in: offset..<(offset + chunkDataSize))
            chunk.append(chunkData)
            chunks.append(chunk)

            offset += chunkDataSize
            sequenceNum += 1
        }

        return chunks
    }

    /// Calculate expected number of chunks for a frame
    static func expectedChunkCount(for frameSize: Int) -> Int {
        let firstChunkSize = maxChunkSize - 6  // Header overhead
        let remainingSize = frameSize - firstChunkSize

        if remainingSize <= 0 {
            return 1
        }

        let subsequentChunkSize = maxChunkSize - 2  // Sequence overhead
        let remainingChunks = (remainingSize + subsequentChunkSize - 1) / subsequentChunkSize

        return 1 + remainingChunks
    }
}
