//
//  DrawingView.swift
//  LEDMatrixController
//
//  Pixel art drawing canvas for LED display
//

import SwiftUI

struct DrawingView: View {
    @ObservedObject var bluetoothManager: BluetoothManager
    @State private var pixels: [[Color]] = Array(repeating: Array(repeating: .black, count: 32), count: 32)
    @State private var selectedColor: Color = .red
    @State private var isErasing = false
    @State private var showColorPicker = false

    // Predefined color palette
    let colorPalette: [Color] = [
        .red, .green, .blue, .yellow, .orange, .purple,
        .pink, .cyan, .white, .gray, .black
    ]

    var body: some View {
        VStack(spacing: 16) {
            // Info text
            if bluetoothManager.isConnected {
                Text("Tap grid to draw • Long press to erase")
                    .font(.caption)
                    .foregroundColor(.secondary)
            } else {
                Text("Connect to display to draw")
                    .font(.caption)
                    .foregroundColor(.red)
            }

            // Drawing grid
            GeometryReader { geometry in
                let gridSize = min(geometry.size.width, geometry.size.height)
                let pixelSize = gridSize / 32

                VStack(spacing: 0) {
                    ForEach(0..<32, id: \.self) { row in
                        HStack(spacing: 0) {
                            ForEach(0..<32, id: \.self) { col in
                                Rectangle()
                                    .fill(pixels[row][col])
                                    .frame(width: pixelSize, height: pixelSize)
                                    .border(Color.gray.opacity(0.2), width: 0.5)
                                    .onTapGesture {
                                        if isErasing {
                                            pixels[row][col] = .black
                                        } else {
                                            pixels[row][col] = selectedColor
                                        }
                                    }
                            }
                        }
                    }
                }
                .frame(width: gridSize, height: gridSize)
                .border(Color.gray, width: 1)
                .position(x: geometry.size.width / 2, y: geometry.size.height / 2)
            }
            .aspectRatio(1, contentMode: .fit)
            .padding()

            // Color palette
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(colorPalette, id: \.self) { color in
                        Circle()
                            .fill(color)
                            .frame(width: 44, height: 44)
                            .overlay(
                                Circle()
                                    .stroke(selectedColor == color ? Color.blue : Color.clear, lineWidth: 3)
                            )
                            .onTapGesture {
                                selectedColor = color
                                isErasing = false
                            }
                    }

                    // Custom color picker button
                    Circle()
                        .fill(LinearGradient(
                            colors: [.red, .yellow, .green, .cyan, .blue, .purple, .red],
                            startPoint: .leading,
                            endPoint: .trailing
                        ))
                        .frame(width: 44, height: 44)
                        .overlay(
                            Image(systemName: "paintpalette.fill")
                                .foregroundColor(.white)
                        )
                        .onTapGesture {
                            showColorPicker = true
                        }
                }
                .padding(.horizontal)
            }

            // Tool buttons
            HStack(spacing: 16) {
                Button(action: { isErasing.toggle() }) {
                    HStack {
                        Image(systemName: "eraser.fill")
                        Text("Erase")
                    }
                    .font(.headline)
                    .foregroundColor(.white)
                    .padding(.vertical, 12)
                    .padding(.horizontal, 24)
                    .background(isErasing ? Color.orange : Color.gray)
                    .cornerRadius(10)
                }

                Button(action: clearCanvas) {
                    HStack {
                        Image(systemName: "trash.fill")
                        Text("Clear")
                    }
                    .font(.headline)
                    .foregroundColor(.white)
                    .padding(.vertical, 12)
                    .padding(.horizontal, 24)
                    .background(Color.red)
                    .cornerRadius(10)
                }

                Button(action: sendToDisplay) {
                    HStack {
                        Image(systemName: "arrow.up.circle.fill")
                        Text("Send")
                    }
                    .font(.headline)
                    .foregroundColor(.white)
                    .padding(.vertical, 12)
                    .padding(.horizontal, 24)
                    .background(Color.blue)
                    .cornerRadius(10)
                }
                .disabled(!bluetoothManager.isConnected)
                .opacity(bluetoothManager.isConnected ? 1.0 : 0.5)
            }
            .padding(.bottom)
        }
        .navigationTitle("Drawing Canvas")
        .navigationBarTitleDisplayMode(.inline)
        .sheet(isPresented: $showColorPicker) {
            ColorPickerSheet(selectedColor: $selectedColor, isPresented: $showColorPicker)
        }
    }

    private func clearCanvas() {
        pixels = Array(repeating: Array(repeating: .black, count: 32), count: 32)
    }

    private func sendToDisplay() {
        guard let config = bluetoothManager.displayConfig else {
            return
        }

        let width = config.grid.totalWidth
        let height = config.grid.totalHeight

        // Convert Color array to RGB data
        var rgbData = Data(count: width * height * 3)

        rgbData.withUnsafeMutableBytes { ptr in
            guard let baseAddress = ptr.baseAddress?.assumingMemoryBound(to: UInt8.self) else { return }

            for row in 0..<height {
                for col in 0..<width {
                    let offset = (row * width + col) * 3
                    let color = pixels[row][col]

                    // Convert SwiftUI Color to RGB components
                    let uiColor = UIColor(color)
                    var red: CGFloat = 0
                    var green: CGFloat = 0
                    var blue: CGFloat = 0
                    var alpha: CGFloat = 0

                    uiColor.getRed(&red, green: &green, blue: &blue, alpha: &alpha)

                    baseAddress[offset + 0] = UInt8(red * 255)
                    baseAddress[offset + 1] = UInt8(green * 255)
                    baseAddress[offset + 2] = UInt8(blue * 255)
                }
            }
        }

        bluetoothManager.sendFrame(rgbData, width: width, height: height)
    }
}

// MARK: - Color Picker Sheet

struct ColorPickerSheet: View {
    @Binding var selectedColor: Color
    @Binding var isPresented: Bool
    @State private var pickerColor: Color

    init(selectedColor: Binding<Color>, isPresented: Binding<Bool>) {
        self._selectedColor = selectedColor
        self._isPresented = isPresented
        self._pickerColor = State(initialValue: selectedColor.wrappedValue)
    }

    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                ColorPicker("Select Color", selection: $pickerColor, supportsOpacity: false)
                    .padding()

                // Preview circle
                Circle()
                    .fill(pickerColor)
                    .frame(width: 100, height: 100)

                Spacer()
            }
            .navigationTitle("Pick Color")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        isPresented = false
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") {
                        selectedColor = pickerColor
                        isPresented = false
                    }
                }
            }
        }
    }
}

// MARK: - Preview

struct DrawingView_Previews: PreviewProvider {
    static var previews: some View {
        NavigationView {
            DrawingView(bluetoothManager: BluetoothManager())
        }
    }
}
