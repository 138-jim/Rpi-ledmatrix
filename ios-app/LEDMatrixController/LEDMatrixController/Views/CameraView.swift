//
//  CameraView.swift
//  LEDMatrixController
//
//  Camera streaming view for LED display
//

import SwiftUI
import AVFoundation

struct CameraView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @StateObject private var cameraManager = CameraManager()

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
                        .disabled(!bluetoothManager.isConnected)
                        .opacity(bluetoothManager.isConnected ? 1.0 : 0.5)
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

                    // Info text
                    if !cameraManager.isStreaming && bluetoothManager.isConnected && cameraManager.permissionGranted {
                        Text("Tap Start to stream your camera to the LED display")
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

        do {
            try cameraManager.setupCamera()
        } catch {
            cameraManager.error = error.localizedDescription
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

            cameraManager.startStreaming { frameData in
                // Send frame to LED display via Bluetooth
                bluetoothManager.sendFrame(frameData, width: width, height: height)
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
