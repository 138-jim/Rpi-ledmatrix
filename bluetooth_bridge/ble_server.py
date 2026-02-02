#!/usr/bin/env python3
"""
BLE Server for LED Matrix Controller

This module implements a Bluetooth Low Energy peripheral that exposes
characteristics for controlling the LED matrix display. It translates
BLE commands to HTTP API calls to the existing LED driver web server.
"""

import asyncio
import json
import logging
import struct
import time
from typing import Optional, Dict, List
import requests
from bleak import BleakGATTCharacteristic, BleakGATTServiceCollection
from bleak.backends.characteristic import GattCharacteristicsFlags

try:
    from bless import (
        BlessServer,
        BlessGATTCharacteristic,
        GATTCharacteristicProperties,
        GATTAttributePermissions
    )
except ImportError:
    print("Error: 'bless' library not found.")
    print("Please install with: pip3 install bless")
    exit(1)

import protocol

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# LED Driver API endpoint
API_BASE_URL = "http://localhost:8080/api"

class FrameAssembler:
    """Handles reassembly of chunked frame data"""

    def __init__(self):
        self.chunks: Dict[int, bytes] = {}
        self.width: Optional[int] = None
        self.height: Optional[int] = None
        self.expected_chunks: Optional[int] = None
        self.last_activity: float = 0
        self.reset()

    def reset(self):
        """Reset frame assembly state"""
        self.chunks = {}
        self.width = None
        self.height = None
        self.expected_chunks = None
        self.last_activity = time.time()

    def add_chunk(self, data: bytes) -> Optional[bytes]:
        """
        Add a chunk of frame data.
        Returns complete frame data if all chunks received, None otherwise.
        """
        if len(data) < 2:
            logger.warning("Chunk too small")
            return None

        # Extract sequence number
        seq_num = struct.unpack('>H', data[0:2])[0]
        chunk_data = data[2:]

        # First chunk contains header with width and height
        if seq_num == 0:
            if len(chunk_data) < 4:
                logger.warning("First chunk missing width/height header")
                return None

            self.width = struct.unpack('>H', chunk_data[0:2])[0]
            self.height = struct.unpack('>H', chunk_data[2:4])[0]
            chunk_data = chunk_data[4:]  # Remove header

            # Calculate expected chunks
            total_bytes = self.width * self.height * 3
            self.expected_chunks = (total_bytes + protocol.MAX_CHUNK_SIZE - 1) // protocol.MAX_CHUNK_SIZE

            logger.info(f"Starting frame assembly: {self.width}x{self.height}, {self.expected_chunks} chunks expected")

        # Store chunk
        self.chunks[seq_num] = chunk_data
        self.last_activity = time.time()

        # Check if we have all chunks
        if self.expected_chunks and len(self.chunks) == self.expected_chunks:
            # Reassemble frame
            frame_data = b''.join([self.chunks[i] for i in range(self.expected_chunks)])

            # Verify size
            expected_size = self.width * self.height * 3
            if len(frame_data) != expected_size:
                logger.error(f"Frame size mismatch: got {len(frame_data)}, expected {expected_size}")
                self.reset()
                return None

            logger.info(f"Frame assembled: {len(frame_data)} bytes")
            result = frame_data
            self.reset()
            return result

        return None

    def is_timeout(self) -> bool:
        """Check if current assembly has timed out"""
        return (time.time() - self.last_activity) > protocol.FRAME_TIMEOUT

    def check_timeout(self):
        """Reset if assembly has timed out"""
        if self.chunks and self.is_timeout():
            logger.warning("Frame assembly timeout, resetting")
            self.reset()


class LEDMatrixBLEServer:
    """BLE Server for LED Matrix control"""

    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.server: Optional[BlessServer] = None
        self.frame_assembler = FrameAssembler()
        self.status_update_task: Optional[asyncio.Task] = None
        self.last_status: Dict = {}

    async def write_brightness(self, characteristic: BlessGATTCharacteristic, value: bytes):
        """Handle brightness control write"""
        if len(value) != 1:
            logger.warning("Invalid brightness value length")
            return

        brightness = value[0]
        logger.info(f"Setting brightness to {brightness}")

        try:
            response = requests.post(
                f"{self.api_url}/brightness",
                json={"brightness": brightness},
                timeout=2
            )
            if response.status_code == 200:
                logger.info(f"Brightness set successfully")
            else:
                logger.error(f"Failed to set brightness: {response.status_code}")
        except Exception as e:
            logger.error(f"Error setting brightness: {e}")

    async def write_pattern(self, characteristic: BlessGATTCharacteristic, value: bytes):
        """Handle pattern selection write"""
        if len(value) != 1:
            logger.warning("Invalid pattern value length")
            return

        pattern_index = value[0]
        pattern_name = protocol.get_pattern_name(pattern_index)

        if not pattern_name:
            logger.warning(f"Invalid pattern index: {pattern_index}")
            return

        logger.info(f"Setting pattern to {pattern_name} (index {pattern_index})")

        try:
            response = requests.post(
                f"{self.api_url}/test-pattern",
                json={"pattern": pattern_name},
                timeout=2
            )
            if response.status_code == 200:
                logger.info(f"Pattern set successfully")
            else:
                logger.error(f"Failed to set pattern: {response.status_code}")
        except Exception as e:
            logger.error(f"Error setting pattern: {e}")

    async def write_game_control(self, characteristic: BlessGATTCharacteristic, value: bytes):
        """Handle game control write"""
        if len(value) != 2:
            logger.warning("Invalid game control value length")
            return

        game_index = value[0]
        action_index = value[1]

        # If action is 0xFF, it's a game start command
        if action_index == 0xFF:
            game_name = protocol.get_game_name(game_index)
            if not game_name:
                logger.warning(f"Invalid game index: {game_index}")
                return

            logger.info(f"Starting game: {game_name}")

            try:
                response = requests.post(
                    f"{self.api_url}/game/start",
                    json={"game_name": game_name},
                    timeout=2
                )
                if response.status_code == 200:
                    logger.info(f"Game started successfully")
                else:
                    logger.error(f"Failed to start game: {response.status_code}")
            except Exception as e:
                logger.error(f"Error starting game: {e}")

        else:
            # It's a game input command
            action_name = protocol.get_action_name(action_index)
            if not action_name:
                logger.warning(f"Invalid action index: {action_index}")
                return

            logger.info(f"Game input: {action_name}")

            try:
                response = requests.post(
                    f"{self.api_url}/game/input",
                    json={"action": action_name},
                    timeout=2
                )
                if response.status_code == 200:
                    logger.info(f"Game input sent successfully")
                else:
                    logger.error(f"Failed to send game input: {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending game input: {e}")

    async def write_power_limit(self, characteristic: BlessGATTCharacteristic, value: bytes):
        """Handle power limit write"""
        if len(value) != 2:
            logger.warning("Invalid power limit value length")
            return

        # Power limit in 0.1A units (e.g., 85 = 8.5A)
        power_units = struct.unpack('>H', value)[0]
        power_amps = power_units / 10.0

        logger.info(f"Setting power limit to {power_amps}A")

        try:
            response = requests.post(
                f"{self.api_url}/power-limit",
                json={
                    "max_current_amps": power_amps,
                    "enabled": True
                },
                timeout=2
            )
            if response.status_code == 200:
                logger.info(f"Power limit set successfully")
            else:
                logger.error(f"Failed to set power limit: {response.status_code}")
        except Exception as e:
            logger.error(f"Error setting power limit: {e}")

    async def write_sleep_schedule(self, characteristic: BlessGATTCharacteristic, value: bytes):
        """Handle sleep schedule write"""
        if len(value) != 4:
            logger.warning("Invalid sleep schedule value length")
            return

        off_hour, off_min, on_hour, on_min = struct.unpack('BBBB', value)

        logger.info(f"Setting sleep schedule: off {off_hour:02d}:{off_min:02d}, on {on_hour:02d}:{on_min:02d}")

        try:
            response = requests.post(
                f"{self.api_url}/sleep-schedule",
                json={
                    "off_time": f"{off_hour:02d}:{off_min:02d}",
                    "on_time": f"{on_hour:02d}:{on_min:02d}",
                    "enabled": True
                },
                timeout=2
            )
            if response.status_code == 200:
                logger.info(f"Sleep schedule set successfully")
            else:
                logger.error(f"Failed to set sleep schedule: {response.status_code}")
        except Exception as e:
            logger.error(f"Error setting sleep schedule: {e}")

    async def write_frame_stream(self, characteristic: BlessGATTCharacteristic, value: bytes):
        """Handle frame stream write (chunked)"""
        # Check for timeout and reset if needed
        self.frame_assembler.check_timeout()

        # Add chunk
        frame_data = self.frame_assembler.add_chunk(value)

        if frame_data:
            # Complete frame received, send to display
            logger.info(f"Sending complete frame to display")

            try:
                response = requests.post(
                    f"{self.api_url}/frame",
                    data=frame_data,
                    headers={'Content-Type': 'application/octet-stream'},
                    timeout=2
                )
                if response.status_code == 200:
                    logger.info(f"Frame sent successfully")
                else:
                    logger.error(f"Failed to send frame: {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending frame: {e}")

    async def read_status(self, characteristic: BlessGATTCharacteristic) -> bytes:
        """Handle status read request"""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=2)
            if response.status_code == 200:
                status_json = json.dumps(response.json())
                return status_json.encode('utf-8')
            else:
                logger.error(f"Failed to get status: {response.status_code}")
                return b'{}'
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return b'{}'

    async def read_config(self, characteristic: BlessGATTCharacteristic) -> bytes:
        """Handle config read request"""
        try:
            response = requests.get(f"{self.api_url}/config", timeout=2)
            if response.status_code == 200:
                config_json = json.dumps(response.json())
                return config_json.encode('utf-8')
            else:
                logger.error(f"Failed to get config: {response.status_code}")
                return b'{}'
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return b'{}'

    async def status_update_loop(self):
        """Background task to poll status and notify clients"""
        while True:
            try:
                await asyncio.sleep(2)  # Poll every 2 seconds

                response = requests.get(f"{self.api_url}/status", timeout=2)
                if response.status_code == 200:
                    status = response.json()

                    # Only notify if status changed
                    if status != self.last_status:
                        self.last_status = status
                        # Note: Notifications would be sent here when clients subscribe
                        logger.debug(f"Status updated: {status}")

            except Exception as e:
                logger.error(f"Error in status update loop: {e}")

    async def run(self):
        """Start the BLE server"""
        logger.info("Starting LED Matrix BLE Server")

        # Create BLE server
        self.server = BlessServer(name="LED Matrix")

        # Add service
        await self.server.add_gatt_service(protocol.SERVICE_UUID)

        # Add characteristics
        # Brightness (write)
        await self.server.add_gatt_characteristic(
            protocol.SERVICE_UUID,
            protocol.CHAR_BRIGHTNESS_UUID,
            GATTCharacteristicProperties.write,
            None,
            GATTAttributePermissions.writeable,
            self.write_brightness
        )

        # Pattern (write)
        await self.server.add_gatt_characteristic(
            protocol.SERVICE_UUID,
            protocol.CHAR_PATTERN_UUID,
            GATTCharacteristicProperties.write,
            None,
            GATTAttributePermissions.writeable,
            self.write_pattern
        )

        # Game Control (write)
        await self.server.add_gatt_characteristic(
            protocol.SERVICE_UUID,
            protocol.CHAR_GAME_CONTROL_UUID,
            GATTCharacteristicProperties.write,
            None,
            GATTAttributePermissions.writeable,
            self.write_game_control
        )

        # Status (read, notify)
        await self.server.add_gatt_characteristic(
            protocol.SERVICE_UUID,
            protocol.CHAR_STATUS_UUID,
            GATTCharacteristicProperties.read | GATTCharacteristicProperties.notify,
            None,
            GATTAttributePermissions.readable,
            self.read_status
        )

        # Config (read)
        await self.server.add_gatt_characteristic(
            protocol.SERVICE_UUID,
            protocol.CHAR_CONFIG_UUID,
            GATTCharacteristicProperties.read,
            None,
            GATTAttributePermissions.readable,
            self.read_config
        )

        # Power Limit (write)
        await self.server.add_gatt_characteristic(
            protocol.SERVICE_UUID,
            protocol.CHAR_POWER_LIMIT_UUID,
            GATTCharacteristicProperties.write,
            None,
            GATTAttributePermissions.writeable,
            self.write_power_limit
        )

        # Sleep Schedule (write)
        await self.server.add_gatt_characteristic(
            protocol.SERVICE_UUID,
            protocol.CHAR_SLEEP_SCHEDULE_UUID,
            GATTCharacteristicProperties.write,
            None,
            GATTAttributePermissions.writeable,
            self.write_sleep_schedule
        )

        # Frame Stream (write)
        await self.server.add_gatt_characteristic(
            protocol.SERVICE_UUID,
            protocol.CHAR_FRAME_STREAM_UUID,
            GATTCharacteristicProperties.write,
            None,
            GATTAttributePermissions.writeable,
            self.write_frame_stream
        )

        # Start server
        await self.server.start()
        logger.info("BLE Server started, advertising as 'LED Matrix'")

        # Start status update loop
        self.status_update_task = asyncio.create_task(self.status_update_loop())

        # Keep running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        finally:
            if self.status_update_task:
                self.status_update_task.cancel()
            await self.server.stop()


async def main():
    """Main entry point"""
    server = LEDMatrixBLEServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
