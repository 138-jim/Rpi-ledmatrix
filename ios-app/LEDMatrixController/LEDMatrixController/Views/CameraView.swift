//
//  CameraView.swift
//  LEDMatrixController
//
//  Camera streaming view for LED display
//

import SwiftUI
import AVFoundation
import PhotosUI
import UniformTypeIdentifiers

/// Transferable wrapper that reliably loads images from PhotosPicker
struct PickableImage: Transferable {
    let image: UIImage

    static var transferRepresentation: some TransferRepresentation {
        DataRepresentation(importedContentType: .image) { data in
            guard let image = UIImage(data: data) else {
                throw CocoaError(.fileReadCorruptFile)
            }
            return PickableImage(image: image)
        }
    }
}

struct CameraView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @StateObject private var cameraManager = CameraManager()
    @State private var selectedPhoto: PhotosPickerItem?
    @State private var isProcessingPhoto = false

    var body: some View {
        ZStack {
            // Camera preview
            if cameraManager.permissionGranted {
                CameraPreviewView(cameraManager: cameraManager)
                    .edgesIgnoringSafeArea(.all)
            } else {
                Color.black
                    .edgesIgnoringSafeArea(.all)
            }

            // Overlay UI
            VStack {
                // Top status bar
                HStack {
                    // Connection status
                    HStack(spacing: 8) {
                        Image(systemName: bluetoothManager.isConnected ? "checkmark.circle.fill" : "exclamationmark.circle.fill")
                            .foregroundColor(bluetoothManager.isConnected ? .green : .red)
                        Text(bluetoothManager.isConnected ? "Connected" : "Not Connected")
                            .font(.caption)
                    }
                    .padding(8)
                    .background(Color.black.opacity(0.6))
                    .cornerRadius(8)

                    Spacer()

                    // FPS counter
                    if cameraManager.isStreaming {
                        HStack(spacing: 4) {
                            Image(systemName: "camera.fill")
                            Text("\(Int(cameraManager.fps)) FPS")
                                .font(.caption)
                                .monospacedDigit()
                        }
                        .padding(8)
                        .background(Color.black.opacity(0.6))
                        .cornerRadius(8)
                        .foregroundColor(.white)
                    }
                }
                .padding()

                Spacer()

                // Bottom controls
                VStack(spacing: 16) {
                    // Permission prompt
                    if !cameraManager.permissionGranted {
                        VStack(spacing: 12) {
                            Image(systemName: "camera.fill")
                                .font(.system(size: 48))
                                .foregroundColor(.white)

                            Text("Camera Access Required")
                                .font(.headline)
                                .foregroundColor(.white)

                            Text("Allow camera access to stream to your LED display")
                                .font(.caption)
                                .foregroundColor(.white.opacity(0.8))
                                .multilineTextAlignment(.center)

                            Button("Enable Camera") {
                                cameraManager.checkPermission()
                            }
                            .buttonStyle(.borderedProminent)
                        }
                        .padding(24)
                        .background(Color.black.opacity(0.7))
                        .cornerRadius(16)
                    }

                    // Stream control button
                    if cameraManager.permissionGranted {
                        Button(action: toggleStreaming) {
                            HStack {
                                Image(systemName: cameraManager.isStreaming ? "stop.fill" : "play.fill")
                                Text(cameraManager.isStreaming ? "Stop Streaming" : "Start Streaming")
                            }
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding(.vertical, 16)
                            .padding(.horizontal, 32)
                            .background(cameraManager.isStreaming ? Color.red : Color.blue)
                            .cornerRadius(12)
                        }
                        .disabled(!bluetoothManager.isConnected || isProcessingPhoto)
                        .opacity(bluetoothManager.isConnected && !isProcessingPhoto ? 1.0 : 0.5)

                        // Photo picker button
                        PhotosPicker(selection: $selectedPhoto, matching: .images) {
                            HStack {
                                Image(systemName: "photo.fill")
                                Text("Select Photo")
                            }
                            .font(.headline)
                            .foregroundColor(.white)
                            .padding(.vertical, 16)
                            .padding(.horizontal, 32)
                            .background(Color.purple)
                            .cornerRadius(12)
                        }
                        .disabled(!bluetoothManager.isConnected || cameraManager.isStreaming || isProcessingPhoto)
                        .opacity(bluetoothManager.isConnected && !cameraManager.isStreaming && !isProcessingPhoto ? 1.0 : 0.5)
                        .onChange(of: selectedPhoto) { oldValue, newValue in
                            if let newValue = newValue {
                                loadAndSendPhoto(newValue)
                            }
                        }
                    }

                    // Error message
                    if let error = cameraManager.error {
                        Text(error)
                            .font(.caption)
                            .foregroundColor(.red)
                            .padding(8)
                            .background(Color.black.opacity(0.7))
                            .cornerRadius(8)
                    }

                    // Processing indicator
                    if isProcessingPhoto {
                        HStack(spacing: 8) {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            Text("Processing photo...")
                                .font(.caption)
                                .foregroundColor(.white)
                        }
                        .padding(8)
                        .background(Color.black.opacity(0.7))
                        .cornerRadius(8)
                    }

                    // Info text
                    if !cameraManager.isStreaming && !isProcessingPhoto && bluetoothManager.isConnected && cameraManager.permissionGranted {
                        Text("Tap Start to stream or Select Photo to display an image")
                            .font(.caption)
                            .foregroundColor(.white)
                            .padding(8)
                            .background(Color.black.opacity(0.6))
                            .cornerRadius(8)
                    }
                }
                .padding()
            }
        }
        .navigationTitle("Camera Stream")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            cameraManager.checkPermission()
            setupCameraIfNeeded()
        }
        .onDisappear {
            cameraManager.stopStreaming()
        }
    }

    private func setupCameraIfNeeded() {
        guard cameraManager.permissionGranted else { return }

        // Setup camera on background thread to avoid blocking UI
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                try self.cameraManager.setupCamera()
            } catch {
                DispatchQueue.main.async {
                    self.cameraManager.error = error.localizedDescription
                }
            }
        }
    }

    private func toggleStreaming() {
        if cameraManager.isStreaming {
            cameraManager.stopStreaming()
        } else {
            guard let config = bluetoothManager.displayConfig else {
                cameraManager.error = "Display configuration not loaded"
                return
            }

            let width = config.grid.totalWidth
            let height = config.grid.totalHeight

            // Start camera streaming directly
            // Camera frames will override any running pattern naturally
            cameraManager.startStreaming { frameData in
                // Send frame to LED display via Bluetooth
                bluetoothManager.sendFrame(frameData, width: width, height: height)
            }
        }
    }

    private func loadUIImage(from item: PhotosPickerItem) async -> UIImage? {
        // Use PickableImage which explicitly requests .image content type
        if let picked = try? await item.loadTransferable(type: PickableImage.self) {
            return picked.image
        }
        // Fallback: try raw Data
        if let data = try? await item.loadTransferable(type: Data.self),
           let image = UIImage(data: data) {
            return image
        }
        return nil
    }

    private func loadAndSendPhoto(_ item: PhotosPickerItem) {
        isProcessingPhoto = true

        Task {
            // Load image data via NSItemProvider for reliable image loading
            guard let uiImage = await loadUIImage(from: item) else {
                await MainActor.run {
                    cameraManager.error = "Failed to load photo"
                    isProcessingPhoto = false
                }
                return
            }

            // Get display dimensions
            guard let config = bluetoothManager.displayConfig else {
                await MainActor.run {
                    cameraManager.error = "Display configuration not loaded"
                    isProcessingPhoto = false
                }
                return
            }

            let width = config.grid.totalWidth
            let height = config.grid.totalHeight
            let targetSize = CGSize(width: width, height: height)

            // Process image to RGB data
            guard let rgbData = ImageProcessor.processImage(uiImage, targetSize: targetSize) else {
                await MainActor.run {
                    cameraManager.error = "Failed to process photo"
                    isProcessingPhoto = false
                }
                return
            }

            // Send to display
            await MainActor.run {
                bluetoothManager.sendFrame(rgbData, width: width, height: height)
                isProcessingPhoto = false
                selectedPhoto = nil  // Clear selection for next time
            }
        }
    }
}

// MARK: - Camera Preview

struct CameraPreviewView: UIViewRepresentable {
    let cameraManager: CameraManager

    func makeUIView(context: Context) -> UIView {
        let view = UIView(frame: .zero)
        view.backgroundColor = .black

        let previewLayer = cameraManager.getPreviewLayer()
        previewLayer.frame = view.bounds
        view.layer.addSublayer(previewLayer)

        // Store layer reference for updates
        context.coordinator.previewLayer = previewLayer

        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {
        // Update preview layer frame when view size changes
        DispatchQueue.main.async {
            context.coordinator.previewLayer?.frame = uiView.bounds
        }
    }

    func makeCoordinator() -> Coordinator {
        Coordinator()
    }

    class Coordinator {
        var previewLayer: AVCaptureVideoPreviewLayer?
    }
}

// MARK: - Preview

struct CameraView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            CameraView(bluetoothManager: BluetoothManager())
        }
    }
}
