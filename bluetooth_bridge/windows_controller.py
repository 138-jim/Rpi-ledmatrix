#!/usr/bin/env python3
"""
Windows BLE Controller for LED Matrix
Uses bleak library for cross-platform BLE support
"""

import asyncio
import struct
import logging
from typing import Optional
from bleak import BleakScanner, BleakClient

import protocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LEDMatrixController:
    """BLE Controller for LED Matrix"""

    def __init__(self):
        self.client: Optional[BleakClient] = None
        self.device_address: Optional[str] = None

    async def scan_for_device(self, timeout: float = 10.0) -> bool:
        """Scan for BLE devices and let user choose"""
        logger.info("Scanning for Bluetooth devices...")
        print("\nScanning for Bluetooth devices (this may take a few seconds)...\n")

        devices = await BleakScanner.discover(timeout=timeout)

        if not devices:
            logger.error("No Bluetooth devices found")
            return False

        # Filter out devices without names and create a list
        named_devices = [(i, dev) for i, dev in enumerate(devices) if dev.name]

        if not named_devices:
            logger.error("No named Bluetooth devices found")
            return False

        # Display devices
        print("="*60)
        print("Available Bluetooth Devices:")
        print("="*60)
        for idx, device in named_devices:
            print(f"{idx + 1}. {device.name} ({device.address})")
        print("="*60)

        # Let user choose
        while True:
            try:
                choice = input(f"\nSelect device (1-{len(named_devices)}) or 0 to cancel: ").strip()
                choice_num = int(choice)

                if choice_num == 0:
                    logger.info("Scan cancelled by user")
                    return False

                if 1 <= choice_num <= len(named_devices):
                    idx, selected_device = named_devices[choice_num - 1]
                    self.device_address = selected_device.address
                    logger.info(f"✅ Selected: {selected_device.name} at {selected_device.address}")
                    return True
                else:
                    print(f"Please enter a number between 1 and {len(named_devices)}")
            except ValueError:
                print("Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\nCancelled by user")
                return False

    async def connect(self) -> bool:
        """Connect to the LED Matrix device"""
        if not self.device_address:
            logger.error("No device address set. Run scan_for_device() first.")
            return False

        logger.info(f"Connecting to {self.device_address}...")

        try:
            self.client = BleakClient(self.device_address)
            await self.client.connect()

            if self.client.is_connected:
                logger.info("✅ Connected successfully")
                return True
            else:
                logger.error("Failed to connect")
                return False
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    async def disconnect(self):
        """Disconnect from device"""
        if self.client and self.client.is_connected:
            await self.client.disconnect()
            logger.info("Disconnected")

    async def set_brightness(self, brightness: int):
        """Set display brightness (0-255)"""
        if not self.client or not self.client.is_connected:
            logger.error("Not connected")
            return

        brightness = max(0, min(255, brightness))
        data = bytes([brightness])

        await self.client.write_gatt_char(protocol.CHAR_BRIGHTNESS_UUID, data)
        logger.info(f"Brightness set to {brightness}")

    async def set_pattern(self, pattern_name: str):
        """Set display pattern by name"""
        if not self.client or not self.client.is_connected:
            logger.error("Not connected")
            return

        pattern_index = protocol.get_pattern_index(pattern_name)
        if pattern_index == -1:
            logger.error(f"Invalid pattern: {pattern_name}")
            return

        data = bytes([pattern_index])
        await self.client.write_gatt_char(protocol.CHAR_PATTERN_UUID, data)
        logger.info(f"Pattern set to {pattern_name} (index {pattern_index})")

    async def start_game(self, game_name: str):
        """Start a game"""
        if not self.client or not self.client.is_connected:
            logger.error("Not connected")
            return

        game_index = protocol.GAMES.index(game_name) if game_name in protocol.GAMES else -1
        if game_index == -1:
            logger.error(f"Invalid game: {game_name}")
            return

        data = bytes([game_index, 0xFF])  # 0xFF signals game start
        await self.client.write_gatt_char(protocol.CHAR_GAME_CONTROL_UUID, data)
        logger.info(f"Started game: {game_name}")

    async def send_game_input(self, action: str):
        """Send game input action"""
        if not self.client or not self.client.is_connected:
            logger.error("Not connected")
            return

        action_index = protocol.ACTIONS.index(action) if action in protocol.ACTIONS else -1
        if action_index == -1:
            logger.error(f"Invalid action: {action}")
            return

        data = bytes([0, action_index])  # Game index 0 for current game
        await self.client.write_gatt_char(protocol.CHAR_GAME_CONTROL_UUID, data)
        logger.info(f"Sent action: {action}")

    async def set_power_limit(self, amps: float):
        """Set power limit in amps"""
        if not self.client or not self.client.is_connected:
            logger.error("Not connected")
            return

        power_units = int(amps * 10)  # Convert to 0.1A units
        data = struct.pack('>H', power_units)

        await self.client.write_gatt_char(protocol.CHAR_POWER_LIMIT_UUID, data)
        logger.info(f"Power limit set to {amps}A")

    async def set_sleep_schedule(self, off_time: str, on_time: str):
        """Set sleep schedule (format: "HH:MM")"""
        if not self.client or not self.client.is_connected:
            logger.error("Not connected")
            return

        off_hour, off_min = map(int, off_time.split(':'))
        on_hour, on_min = map(int, on_time.split(':'))

        data = bytes([off_hour, off_min, on_hour, on_min])
        await self.client.write_gatt_char(protocol.CHAR_SLEEP_SCHEDULE_UUID, data)
        logger.info(f"Sleep schedule set: off {off_time}, on {on_time}")

    async def get_status(self) -> Optional[str]:
        """Read status from device"""
        if not self.client or not self.client.is_connected:
            logger.error("Not connected")
            return None

        data = await self.client.read_gatt_char(protocol.CHAR_STATUS_UUID)
        status = data.decode('utf-8')
        logger.info(f"Status: {status}")
        return status

    async def get_config(self) -> Optional[str]:
        """Read config from device"""
        if not self.client or not self.client.is_connected:
            logger.error("Not connected")
            return None

        data = await self.client.read_gatt_char(protocol.CHAR_CONFIG_UUID)
        config = data.decode('utf-8')
        logger.info(f"Config: {config}")
        return config


async def interactive_menu(controller: LEDMatrixController):
    """Interactive menu for controlling the LED matrix"""

    while True:
        print("\n" + "="*50)
        print("LED Matrix Controller")
        print("="*50)
        print("1. Set Brightness")
        print("2. Set Pattern")
        print("3. Start Game")
        print("4. Send Game Input")
        print("5. Set Power Limit")
        print("6. Set Sleep Schedule")
        print("7. Get Status")
        print("8. Get Config")
        print("9. List Available Patterns")
        print("0. Exit")
        print("="*50)

        choice = input("\nEnter choice: ").strip()

        try:
            if choice == "1":
                brightness = int(input("Enter brightness (0-255): "))
                await controller.set_brightness(brightness)

            elif choice == "2":
                pattern = input(f"Enter pattern name: ").strip()
                await controller.set_pattern(pattern)

            elif choice == "3":
                print(f"Available games: {', '.join(protocol.GAMES)}")
                game = input("Enter game name: ").strip()
                await controller.start_game(game)

            elif choice == "4":
                print(f"Available actions: {', '.join(protocol.ACTIONS)}")
                action = input("Enter action: ").strip()
                await controller.send_game_input(action)

            elif choice == "5":
                amps = float(input("Enter power limit in amps: "))
                await controller.set_power_limit(amps)

            elif choice == "6":
                off_time = input("Enter off time (HH:MM): ").strip()
                on_time = input("Enter on time (HH:MM): ").strip()
                await controller.set_sleep_schedule(off_time, on_time)

            elif choice == "7":
                await controller.get_status()

            elif choice == "8":
                await controller.get_config()

            elif choice == "9":
                print("\nAvailable Patterns:")
                for i, pattern in enumerate(protocol.PATTERNS):
                    print(f"  {i}: {pattern}")

            elif choice == "0":
                print("Exiting...")
                break

            else:
                print("Invalid choice")

        except Exception as e:
            logger.error(f"Error: {e}")


async def main():
    """Main entry point"""
    controller = LEDMatrixController()

    # Scan for device
    if not await controller.scan_for_device():
        logger.error("Could not find LED Matrix device")
        return

    # Connect
    if not await controller.connect():
        logger.error("Could not connect to device")
        return

    try:
        # Run interactive menu
        await interactive_menu(controller)
    finally:
        # Disconnect
        await controller.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
