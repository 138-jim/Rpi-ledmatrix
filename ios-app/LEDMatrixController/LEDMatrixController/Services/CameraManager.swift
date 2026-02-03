//
//  CameraManager.swift
//  LEDMatrixController
//
//  Camera capture manager for streaming to LED display
//

import AVFoundation
import UIKit
import Combine

class CameraManager: NSObject, ObservableObject {

    // MARK: - Published Properties

    @Published var isStreaming = false
    @Published var permissionGranted = false
    @Published var error: String?
    @Published var fps: Double = 0

    // MARK: - Private Properties

    private let captureSession = AVCaptureSession()
    private let videoOutput = AVCaptureVideoDataOutput()
    private let captureQueue = DispatchQueue(label: "com.ledmatrix.camera", qos: .userInitiated)

    private var frameCallback: ((Data) -> Void)?
    private var lastFrameTime = Date()
    private var frameCount = 0

    // MARK: - Configuration

    private let targetSize = CGSize(width: 32, height: 32)
    private let targetFPS: Double = 15  // Limit to 15 FPS to avoid overwhelming BLE
    private let minFrameInterval: TimeInterval

    override init() {
        self.minFrameInterval = 1.0 / targetFPS
        super.init()
    }

    // MARK: - Public Methods

    /// Check camera permission status
    func checkPermission() {
        switch AVCaptureDevice.authorizationStatus(for: .video) {
        case .authorized:
            permissionGranted = true
        case .notDetermined:
            requestPermission()
        case .denied, .restricted:
            permissionGranted = false
            error = "Camera access denied. Please enable in Settings."
        @unknown default:
            permissionGranted = false
            error = "Unknown camera permission status"
        }
    }

    /// Request camera permission
    private func requestPermission() {
        AVCaptureDevice.requestAccess(for: .video) { [weak self] granted in
            DispatchQueue.main.async {
                self?.permissionGranted = granted
                if !granted {
                    self?.error = "Camera access denied"
                }
            }
        }
    }

    /// Setup camera capture session
    func setupCamera() throws {
        guard permissionGranted else {
            throw CameraError.permissionDenied
        }

        // Configure session for lower quality (we only need 32x32)
        captureSession.beginConfiguration()
        captureSession.sessionPreset = .medium

        // Get front camera
        guard let camera = AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .front) else {
            throw CameraError.cameraNotAvailable
        }

        // Add camera input
        let input = try AVCaptureDeviceInput(device: camera)
        if captureSession.canAddInput(input) {
            captureSession.addInput(input)
        } else {
            throw CameraError.cannotAddInput
        }

        // Configure video output
        videoOutput.setSampleBufferDelegate(self, queue: captureQueue)
        videoOutput.alwaysDiscardsLateVideoFrames = true

        // Use 32-bit BGRA format for easier processing
        videoOutput.videoSettings = [
            kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32BGRA
        ]

        if captureSession.canAddOutput(videoOutput) {
            captureSession.addOutput(videoOutput)
        } else {
            throw CameraError.cannotAddOutput
        }

        // Set video orientation (iOS 17+ uses rotation angle instead)
        if let connection = videoOutput.connection(with: .video) {
            if #available(iOS 17.0, *) {
                connection.videoRotationAngle = 0  // Portrait
            } else {
                if connection.isVideoOrientationSupported {
                    connection.videoOrientation = .portrait
                }
            }
        }

        captureSession.commitConfiguration()
    }

    /// Start camera streaming
    func startStreaming(onFrame: @escaping (Data) -> Void) {
        guard permissionGranted else {
            error = "Camera permission not granted"
            return
        }

        frameCallback = onFrame

        if !captureSession.isRunning {
            DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                self?.captureSession.startRunning()
                DispatchQueue.main.async {
                    self?.isStreaming = true
                    self?.error = nil
                }
            }
        }
    }

    /// Stop camera streaming
    func stopStreaming() {
        if captureSession.isRunning {
            DispatchQueue.global(qos: .userInitiated).async { [weak self] in
                self?.captureSession.stopRunning()
                DispatchQueue.main.async {
                    self?.isStreaming = false
                    self?.frameCallback = nil
                }
            }
        }
    }

    /// Get preview layer for UI
    func getPreviewLayer() -> AVCaptureVideoPreviewLayer {
        let previewLayer = AVCaptureVideoPreviewLayer(session: captureSession)
        previewLayer.videoGravity = .resizeAspectFill
        return previewLayer
    }
}

// MARK: - AVCaptureVideoDataOutputSampleBufferDelegate

extension CameraManager: AVCaptureVideoDataOutputSampleBufferDelegate {

    func captureOutput(_ output: AVCaptureOutput, didOutput sampleBuffer: CMSampleBuffer, from connection: AVCaptureConnection) {
        // Throttle frame rate
        let now = Date()
        let elapsed = now.timeIntervalSince(lastFrameTime)

        guard elapsed >= minFrameInterval else {
            return  // Skip frame to maintain target FPS
        }

        lastFrameTime = now

        // Process frame
        guard let rgbData = ImageProcessor.processCameraFrame(sampleBuffer, targetSize: targetSize) else {
            return
        }

        // Send to callback
        frameCallback?(rgbData)

        // Update FPS counter
        frameCount += 1
        if frameCount % 30 == 0 {  // Update FPS every 30 frames
            DispatchQueue.main.async { [weak self] in
                self?.fps = 1.0 / elapsed
            }
        }
    }
}

// MARK: - Camera Errors

enum CameraError: LocalizedError {
    case permissionDenied
    case cameraNotAvailable
    case cannotAddInput
    case cannotAddOutput

    var errorDescription: String? {
        switch self {
        case .permissionDenied:
            return "Camera permission denied"
        case .cameraNotAvailable:
            return "Camera not available"
        case .cannotAddInput:
            return "Cannot add camera input"
        case .cannotAddOutput:
            return "Cannot add video output"
        }
    }
}
