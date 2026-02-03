//
//  BluetoothManager.swift
//  LEDMatrixController
//
//  Core Bluetooth manager for LED Matrix communication
//

import Foundation
import CoreBluetooth
import Combine

/// Main Bluetooth manager coordinating all BLE communication
class BluetoothManager: NSObject, ObservableObject {

    // MARK: - Published Properties

    @Published var isScanning = false
    @Published var isConnected = false
    @Published var discoveredPeripherals: [CBPeripheral] = []
    @Published var displayStatus: DisplayStatus?
    @Published var displayConfig: LEDDisplayConfig?
    @Published var connectionError: String?
    @Published var availablePatterns: [String] = []
    @Published var availableGames: [String] = []
    @Published var deviceCapabilities: DeviceCapabilities?
    @Published var powerLimitAmps: Float = 80.0
    @Published var sleepSchedule: SleepSchedule = .defaultSchedule

    // MARK: - Private Properties

    private var centralManager: CBCentralManager!
    private var connectedPeripheral: CBPeripheral?

    // Characteristic references
    private var brightnessCharacteristic: CBCharacteristic?
    private var patternCharacteristic: CBCharacteristic?
    private var gameControlCharacteristic: CBCharacteristic?
    private var statusCharacteristic: CBCharacteristic?
    private var configCharacteristic: CBCharacteristic?
    private var powerLimitCharacteristic: CBCharacteristic?
    private var sleepScheduleCharacteristic: CBCharacteristic?
    private var frameStreamCharacteristic: CBCharacteristic?
    private var patternListCharacteristic: CBCharacteristic?
    private var gameListCharacteristic: CBCharacteristic?
    private var capabilitiesCharacteristic: CBCharacteristic?

    // Command queue for reliable delivery
    private var commandQueue: [(Data, CBCharacteristic)] = []
    private var isProcessingQueue = false

    // MARK: - Initialization

    override init() {
        super.init()
        centralManager = CBCentralManager(delegate: self, queue: nil)
    }

    // MARK: - Public Methods

    /// Start scanning for LED Matrix devices
    func startScanning() {
        guard centralManager.state == .poweredOn else {
            connectionError = "Bluetooth is not available"
            return
        }

        isScanning = true
        discoveredPeripherals.removeAll()
        connectionError = nil

        // Scan for devices advertising the LED Matrix service
        centralManager.scanForPeripherals(
            withServices: [BLEProtocol.serviceUUID],
            options: [CBCentralManagerScanOptionAllowDuplicatesKey: false]
        )

        print("🔍 Started scanning for LED Matrix devices...")
    }

    /// Stop scanning
    func stopScanning() {
        centralManager.stopScan()
        isScanning = false
        print("⏹ Stopped scanning")
    }

    /// Connect to a discovered peripheral
    func connect(to peripheral: CBPeripheral) {
        stopScanning()
        connectionError = nil

        print("🔌 Connecting to \(peripheral.name ?? "Unknown")...")
        centralManager.connect(peripheral, options: nil)
    }

    /// Disconnect from current peripheral
    func disconnect() {
        guard let peripheral = connectedPeripheral else { return }

        print("🔌 Disconnecting...")
        centralManager.cancelPeripheralConnection(peripheral)
    }

    /// Set display brightness (0-255)
    func setBrightness(_ value: UInt8) {
        guard let characteristic = brightnessCharacteristic else { return }

        let data = Data([value])
        writeValue(data, to: characteristic)
        print("💡 Setting brightness to \(value)")
    }

    /// Select pattern by index (0-36)
    func setPattern(_ patternIndex: UInt8) {
        guard let characteristic = patternCharacteristic else { return }

        let data = Data([patternIndex])
        writeValue(data, to: characteristic)

        if let pattern = DisplayPattern.pattern(at: Int(patternIndex)) {
            print("🎨 Setting pattern to \(pattern.name)")
        }
    }

    /// Start a game
    func startGame(_ gameIndex: UInt8) {
        guard let characteristic = gameControlCharacteristic else { return }

        // 0xFF indicates game start
        let data = Data([gameIndex, 0xFF])
        writeValue(data, to: characteristic)

        if let game = Game.game(at: Int(gameIndex)) {
            print("🎮 Starting game: \(game.displayName)")
        }
    }

    /// Send game input
    func sendGameInput(_ action: GameAction) {
        guard let characteristic = gameControlCharacteristic else { return }

        // Use game index 0 (Snake) as default - you can make this configurable
        let data = Data([0, action.rawValue])
        writeValue(data, to: characteristic)

        print("🕹 Game input: \(action)")
    }

    /// Set power limit in amps
    func setPowerLimit(amps: Float) {
        guard let characteristic = powerLimitCharacteristic else { return }

        // Convert to 0.1A units
        let units = UInt16(amps * 10.0)
        var data = Data()
        data.append(contentsOf: withUnsafeBytes(of: units.bigEndian) { Array($0) })

        writeValue(data, to: characteristic)
        print("⚡️ Setting power limit to \(amps)A")
    }

    /// Set sleep schedule
    func setSleepSchedule(offHour: UInt8, offMin: UInt8, onHour: UInt8, onMin: UInt8, enabled: Bool = true) {
        guard let characteristic = sleepScheduleCharacteristic else { return }

        let data = Data([offHour, offMin, onHour, onMin])
        writeValue(data, to: characteristic)

        // Update local state
        let calendar = Calendar.current
        let offTime = calendar.date(from: DateComponents(hour: Int(offHour), minute: Int(offMin))) ?? Date()
        let onTime = calendar.date(from: DateComponents(hour: Int(onHour), minute: Int(onMin))) ?? Date()

        DispatchQueue.main.async {
            self.sleepSchedule = SleepSchedule(
                enabled: enabled,
                offTime: offTime,
                onTime: onTime,
                isSleeping: self.sleepSchedule.isSleeping
            )
        }

        print("🌙 Setting sleep schedule: off \(offHour):\(offMin), on \(onHour):\(onMin), enabled: \(enabled)")
    }

    /// Send a complete frame
    func sendFrame(_ frameData: Data, width: Int, height: Int) {
        guard let characteristic = frameStreamCharacteristic else { return }

        let chunks = FrameChunker.chunkFrame(frameData, width: width, height: height)

        print("🖼 Sending frame (\(width)x\(height)) in \(chunks.count) chunks")

        for chunk in chunks {
            writeValue(chunk, to: characteristic)
            // Small delay between chunks to avoid overwhelming BLE buffer
            usleep(5000) // 5ms
        }
    }

    /// Request status update
    func requestStatus() {
        guard let characteristic = statusCharacteristic,
              let peripheral = connectedPeripheral else { return }

        peripheral.readValue(for: characteristic)
    }

    /// Request configuration
    func requestConfig() {
        guard let characteristic = configCharacteristic,
              let peripheral = connectedPeripheral else { return }

        peripheral.readValue(for: characteristic)
    }

    /// Request pattern list from device
    func requestPatternList() {
        guard let characteristic = patternListCharacteristic,
              let peripheral = connectedPeripheral else { return }

        peripheral.readValue(for: characteristic)
        print("📋 Requesting pattern list from device...")
    }

    /// Request game list from device
    func requestGameList() {
        guard let characteristic = gameListCharacteristic,
              let peripheral = connectedPeripheral else { return }

        peripheral.readValue(for: characteristic)
        print("🎮 Requesting game list from device...")
    }

    /// Request current power limit from device
    func requestPowerLimit() {
        guard let characteristic = powerLimitCharacteristic,
              let peripheral = connectedPeripheral else { return }

        peripheral.readValue(for: characteristic)
        print("⚡️ Requesting power limit from device...")
    }

    // MARK: - Private Methods

    private func writeValue(_ data: Data, to characteristic: CBCharacteristic) {
        guard let peripheral = connectedPeripheral else { return }

        // Add to queue
        commandQueue.append((data, characteristic))

        // Process queue if not already processing
        if !isProcessingQueue {
            processCommandQueue()
        }
    }

    private func processCommandQueue() {
        guard !commandQueue.isEmpty,
              let peripheral = connectedPeripheral else {
            isProcessingQueue = false
            return
        }

        isProcessingQueue = true
        let (data, characteristic) = commandQueue.removeFirst()

        peripheral.writeValue(data, for: characteristic, type: .withoutResponse)

        // Small delay before next command
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.01) { [weak self] in
            self?.processCommandQueue()
        }
    }
}

// MARK: - CBCentralManagerDelegate

extension BluetoothManager: CBCentralManagerDelegate {

    func centralManagerDidUpdateState(_ central: CBCentralManager) {
        switch central.state {
        case .poweredOn:
            print("✅ Bluetooth powered on")
        case .poweredOff:
            connectionError = "Bluetooth is powered off"
            print("❌ Bluetooth powered off")
        case .unsupported:
            connectionError = "Bluetooth is not supported on this device"
            print("❌ Bluetooth not supported")
        case .unauthorized:
            connectionError = "Bluetooth access not authorized"
            print("❌ Bluetooth not authorized")
        case .resetting:
            print("⚠️ Bluetooth resetting")
        case .unknown:
            print("⚠️ Bluetooth state unknown")
        @unknown default:
            print("⚠️ Unknown Bluetooth state")
        }
    }

    func centralManager(_ central: CBCentralManager, didDiscover peripheral: CBPeripheral,
                       advertisementData: [String : Any], rssi RSSI: NSNumber) {

        // Check if already discovered
        if !discoveredPeripherals.contains(where: { $0.identifier == peripheral.identifier }) {
            discoveredPeripherals.append(peripheral)
            print("🔍 Discovered: \(peripheral.name ?? "Unknown") (RSSI: \(RSSI))")
        }
    }

    func centralManager(_ central: CBCentralManager, didConnect peripheral: CBPeripheral) {
        print("✅ Connected to \(peripheral.name ?? "Unknown")")

        connectedPeripheral = peripheral
        peripheral.delegate = self
        isConnected = true
        connectionError = nil

        // Discover services
        peripheral.discoverServices([BLEProtocol.serviceUUID])
    }

    func centralManager(_ central: CBCentralManager, didFailToConnect _: CBPeripheral, error: Error?) {
        print("❌ Failed to connect: \(error?.localizedDescription ?? "Unknown error")")
        connectionError = "Failed to connect: \(error?.localizedDescription ?? "Unknown error")"
        isConnected = false
    }

    func centralManager(_ central: CBCentralManager, didDisconnectPeripheral peripheral: CBPeripheral, error: Error?) {
        print("🔌 Disconnected from \(peripheral.name ?? "Unknown")")

        if let error = error {
            print("❌ Disconnect error: \(error.localizedDescription)")
            connectionError = "Disconnected: \(error.localizedDescription)"
        }

        isConnected = false
        connectedPeripheral = nil

        // Clear characteristics
        brightnessCharacteristic = nil
        patternCharacteristic = nil
        gameControlCharacteristic = nil
        statusCharacteristic = nil
        configCharacteristic = nil
        powerLimitCharacteristic = nil
        sleepScheduleCharacteristic = nil
        frameStreamCharacteristic = nil
        patternListCharacteristic = nil
        gameListCharacteristic = nil
        capabilitiesCharacteristic = nil

        // Clear dynamic data
        availablePatterns = []
        availableGames = []
        deviceCapabilities = nil
        powerLimitAmps = 80.0
        sleepSchedule = .defaultSchedule
    }
}

// MARK: - CBPeripheralDelegate

extension BluetoothManager: CBPeripheralDelegate {

    func peripheral(_ peripheral: CBPeripheral, didDiscoverServices error: Error?) {
        guard error == nil else {
            print("❌ Error discovering services: \(error!.localizedDescription)")
            return
        }

        guard let services = peripheral.services else { return }

        for service in services {
            print("🔍 Discovered service: \(service.uuid)")

            if service.uuid == BLEProtocol.serviceUUID {
                // Discover all characteristics
                peripheral.discoverCharacteristics(nil, for: service)
            }
        }
    }

    func peripheral(_ peripheral: CBPeripheral, didDiscoverCharacteristicsFor service: CBService, error: Error?) {
        guard error == nil else {
            print("❌ Error discovering characteristics: \(error!.localizedDescription)")
            return
        }

        guard let characteristics = service.characteristics else { return }

        for characteristic in characteristics {
            print("🔍 Discovered characteristic: \(characteristic.uuid)")

            // Store characteristic references
            switch characteristic.uuid {
            case BLEProtocol.brightnessUUID:
                brightnessCharacteristic = characteristic
            case BLEProtocol.patternUUID:
                patternCharacteristic = characteristic
            case BLEProtocol.gameControlUUID:
                gameControlCharacteristic = characteristic
            case BLEProtocol.statusUUID:
                statusCharacteristic = characteristic
                // Subscribe to status notifications
                peripheral.setNotifyValue(true, for: characteristic)
            case BLEProtocol.configUUID:
                configCharacteristic = characteristic
                // Read config once
                peripheral.readValue(for: characteristic)
            case BLEProtocol.powerLimitUUID:
                powerLimitCharacteristic = characteristic
                // Read power limit once on connection
                peripheral.readValue(for: characteristic)
            case BLEProtocol.sleepScheduleUUID:
                sleepScheduleCharacteristic = characteristic
            case BLEProtocol.frameStreamUUID:
                frameStreamCharacteristic = characteristic
            case BLEProtocol.patternListUUID:
                patternListCharacteristic = characteristic
                // Read pattern list once on connection
                peripheral.readValue(for: characteristic)
            case BLEProtocol.gameListUUID:
                gameListCharacteristic = characteristic
                // Read game list once on connection
                peripheral.readValue(for: characteristic)
            case BLEProtocol.capabilitiesUUID:
                capabilitiesCharacteristic = characteristic
                // Read capabilities once on connection
                peripheral.readValue(for: characteristic)
            default:
                break
            }
        }

        print("✅ All characteristics discovered and configured")
    }

    func peripheral(_ peripheral: CBPeripheral, didUpdateValueFor characteristic: CBCharacteristic, error: Error?) {
        guard error == nil else {
            print("❌ Error reading characteristic: \(error!.localizedDescription)")
            return
        }

        guard let data = characteristic.value else { return }

        // Handle characteristic updates
        switch characteristic.uuid {
        case BLEProtocol.statusUUID:
            // Parse status JSON
            if let jsonString = String(data: data, encoding: .utf8),
               let jsonData = jsonString.data(using: .utf8) {
                do {
                    let status = try JSONDecoder().decode(DisplayStatus.self, from: jsonData)
                    DispatchQueue.main.async {
                        self.displayStatus = status
                    }
                } catch {
                    print("❌ Failed to parse status: \(error)")
                }
            }

        case BLEProtocol.configUUID:
            // Parse config JSON
            if let jsonString = String(data: data, encoding: .utf8),
               let jsonData = jsonString.data(using: .utf8) {
                do {
                    let config = try JSONDecoder().decode(LEDDisplayConfig.self, from: jsonData)
                    DispatchQueue.main.async {
                        self.displayConfig = config
                    }
                    print("✅ Display config loaded: \(config.grid.totalWidth)x\(config.grid.totalHeight)")
                } catch {
                    print("❌ Failed to parse config: \(error)")
                }
            }

        case BLEProtocol.patternListUUID:
            // Parse pattern list JSON
            if let jsonString = String(data: data, encoding: .utf8),
               let jsonData = jsonString.data(using: .utf8) {
                do {
                    let patternList = try JSONDecoder().decode(PatternListResponse.self, from: jsonData)
                    DispatchQueue.main.async {
                        self.availablePatterns = patternList.patterns
                    }
                    print("✅ Pattern list loaded: \(patternList.count) patterns")
                    print("📋 Available patterns: \(patternList.patterns.joined(separator: ", "))")
                } catch {
                    print("❌ Failed to parse pattern list: \(error)")
                }
            }

        case BLEProtocol.gameListUUID:
            // Parse game list JSON
            if let jsonString = String(data: data, encoding: .utf8),
               let jsonData = jsonString.data(using: .utf8) {
                do {
                    let gameList = try JSONDecoder().decode(GameListResponse.self, from: jsonData)
                    DispatchQueue.main.async {
                        self.availableGames = gameList.games
                    }
                    print("✅ Game list loaded: \(gameList.count) games")
                    print("🎮 Available games: \(gameList.games.joined(separator: ", "))")
                } catch {
                    print("❌ Failed to parse game list: \(error)")
                }
            }

        case BLEProtocol.capabilitiesUUID:
            // Parse capabilities JSON
            if let jsonString = String(data: data, encoding: .utf8),
               let jsonData = jsonString.data(using: .utf8) {
                do {
                    let capabilities = try JSONDecoder().decode(DeviceCapabilities.self, from: jsonData)
                    DispatchQueue.main.async {
                        self.deviceCapabilities = capabilities
                    }
                    print("✅ Device capabilities loaded:")
                    print("   - Firmware: \(capabilities.firmwareVersion)")
                    print("   - Games: \(capabilities.hasGames)")
                    print("   - Patterns: \(capabilities.hasPatterns)")
                    print("   - Frame Streaming: \(capabilities.hasFrameStreaming)")
                    print("   - Power Limiter: \(capabilities.hasPowerLimiter)")
                    print("   - Sleep Scheduler: \(capabilities.hasSleepScheduler)")
                    print("   - Brightness Control: \(capabilities.hasBrightnessControl)")
                } catch {
                    print("❌ Failed to parse capabilities: \(error)")
                }
            }

        case BLEProtocol.powerLimitUUID:
            // Parse power limit (2 bytes, big-endian, in 0.1A units)
            if data.count == 2 {
                let powerUnits = data.withUnsafeBytes { $0.load(as: UInt16.self).bigEndian }
                let powerAmps = Float(powerUnits) / 10.0
                DispatchQueue.main.async {
                    self.powerLimitAmps = powerAmps
                }
                print("✅ Power limit loaded: \(powerAmps)A")
            } else {
                print("❌ Invalid power limit data length: \(data.count)")
            }

        default:
            break
        }
    }
}
