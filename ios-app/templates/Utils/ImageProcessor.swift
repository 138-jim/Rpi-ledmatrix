//
//  ImageProcessor.swift
//  LEDMatrixController
//
//  Utility for processing images for LED display
//

import UIKit
import CoreImage
import AVFoundation

/// Handles image processing for LED matrix display
struct ImageProcessor {

    /// Process UIImage to RGB data for display
    /// - Parameters:
    ///   - image: Source image
    ///   - size: Target size (default 32x32)
    /// - Returns: Raw RGB data (width × height × 3 bytes), or nil if processing fails
    static func processImage(_ image: UIImage, targetSize: CGSize = CGSize(width: 32, height: 32)) -> Data? {
        // Resize image
        guard let resizedImage = resize(image, to: targetSize) else { return nil }

        // Extract RGB data
        return extractRGBData(from: resizedImage)
    }

    /// Resize image to target size
    private static func resize(_ image: UIImage, to size: CGSize) -> UIImage? {
        UIGraphicsBeginImageContextWithOptions(size, false, 1.0)
        defer { UIGraphicsEndImageContext() }

        image.draw(in: CGRect(origin: .zero, size: size))
        return UIGraphicsGetImageFromCurrentImageContext()
    }

    /// Extract raw RGB data from image
    private static func extractRGBData(from image: UIImage) -> Data? {
        guard let cgImage = image.cgImage else { return nil }

        let width = cgImage.width
        let height = cgImage.height
        let bytesPerPixel = 3
        let bytesPerRow = bytesPerPixel * width
        let bitsPerComponent = 8

        // Create buffer for RGB data
        var rgbData = Data(count: width * height * bytesPerPixel)

        rgbData.withUnsafeMutableBytes { ptr in
            guard let context = CGContext(
                data: ptr.baseAddress,
                width: width,
                height: height,
                bitsPerComponent: bitsPerComponent,
                bytesPerRow: bytesPerRow,
                space: CGColorSpaceCreateDeviceRGB(),
                bitmapInfo: CGImageAlphaInfo.none.rawValue
            ) else { return }

            context.draw(cgImage, in: CGRect(x: 0, y: 0, width: width, height: height))
        }

        return rgbData
    }

    /// Apply dithering for better LED display quality
    /// - Parameter image: Source image
    /// - Returns: Dithered image
    static func ditherImage(_ image: UIImage) -> UIImage? {
        // Simple Floyd-Steinberg dithering
        // For now, return original - can implement full dithering if needed
        return image
    }

    /// Process camera sample buffer to RGB data
    /// - Parameters:
    ///   - sampleBuffer: Camera sample buffer
    ///   - size: Target size
    /// - Returns: RGB data, or nil if processing fails
    static func processCameraFrame(_ sampleBuffer: CMSampleBuffer, targetSize: CGSize = CGSize(width: 32, height: 32)) -> Data? {
        guard let imageBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else {
            return nil
        }

        let ciImage = CIImage(cvPixelBuffer: imageBuffer)
        let context = CIContext()

        guard let cgImage = context.createCGImage(ciImage, from: ciImage.extent) else {
            return nil
        }

        let image = UIImage(cgImage: cgImage)
        return processImage(image, targetSize: targetSize)
    }

    /// Create test pattern (useful for debugging)
    static func createTestPattern(width: Int = 32, height: Int = 32) -> Data {
        var data = Data(count: width * height * 3)

        data.withUnsafeMutableBytes { ptr in
            guard let baseAddress = ptr.baseAddress?.assumingMemoryBound(to: UInt8.self) else { return }

            for y in 0..<height {
                for x in 0..<width {
                    let offset = (y * width + x) * 3

                    // Create gradient pattern
                    baseAddress[offset + 0] = UInt8((x * 255) / width)      // R
                    baseAddress[offset + 1] = UInt8((y * 255) / height)     // G
                    baseAddress[offset + 2] = UInt8(128)                     // B
                }
            }
        }

        return data
    }

    /// Create solid color frame
    static func createSolidColor(r: UInt8, g: UInt8, b: UInt8, width: Int = 32, height: Int = 32) -> Data {
        var data = Data(count: width * height * 3)

        data.withUnsafeMutableBytes { ptr in
            guard let baseAddress = ptr.baseAddress?.assumingMemoryBound(to: UInt8.self) else { return }

            for i in 0..<(width * height) {
                let offset = i * 3
                baseAddress[offset + 0] = r
                baseAddress[offset + 1] = g
                baseAddress[offset + 2] = b
            }
        }

        return data
    }
}
