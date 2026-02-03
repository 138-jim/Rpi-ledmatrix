#!/usr/bin/env python3
"""
BLE Server for LED Matrix Controller using bluezero

This module implements a Bluetooth Low Energy peripheral using the bluezero
library, which provides a clean API for BlueZ on Linux/Raspberry Pi.
"""

import json
import logging
import struct
import time
from typing import Optional, Dict
import requests
from bluezero import peripheral
from bluezero import adapter

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
    """BLE Server for LED Matrix control using bluezero"""

    def __init__(self, api_url: str = API_BASE_URL):
        self.api_url = api_url
        self.frame_assembler = FrameAssembler()

        # Get adapter
        adapters = list(adapter.Adapter.available())
        if not adapters:
            raise RuntimeError("No Bluetooth adapters found")

        self.adapter_addr = adapters[0].address
        logger.info(f"Using Bluetooth adapter: {self.adapter_addr}")

        # Create peripheral
        self.peripheral = peripheral.Peripheral(
            self.adapter_addr,
            local_name='LED Matrix',
            appearance=0x0000  # Generic device
        )

        # Service ID counter
        self.srv_id = 1

        # Setup GATT services and characteristics
        self._setup_gatt()

    def _setup_gatt(self):
        """Setup GATT services and characteristics"""

        # Add LED Matrix service
        self.peripheral.add_service(
            srv_id=self.srv_id,
            uuid=protocol.SERVICE_UUID,
            primary=True
        )

        char_id = 1

        # Brightness characteristic (write)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_BRIGHTNESS_UUID,
            value=[],
            notifying=False,
            flags=['write', 'write-without-response'],
            write_callback=self.on_brightness_write
        )
        char_id += 1

        # Pattern characteristic (write)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_PATTERN_UUID,
            value=[],
            notifying=False,
            flags=['write', 'write-without-response'],
            write_callback=self.on_pattern_write
        )
        char_id += 1

        # Game Control characteristic (write)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_GAME_CONTROL_UUID,
            value=[],
            notifying=False,
            flags=['write', 'write-without-response'],
            write_callback=self.on_game_control_write
        )
        char_id += 1

        # Status characteristic (read, notify)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_STATUS_UUID,
            value=[],
            notifying=False,
            flags=['read', 'notify'],
            read_callback=self.on_status_read
        )
        char_id += 1

        # Config characteristic (read)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_CONFIG_UUID,
            value=[],
            notifying=False,
            flags=['read'],
            read_callback=self.on_config_read
        )
        char_id += 1

        # Power Limit characteristic (read/write)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_POWER_LIMIT_UUID,
            value=[],
            notifying=False,
            flags=['read', 'write', 'write-without-response'],
            read_callback=self.on_power_limit_read,
            write_callback=self.on_power_limit_write
        )
        char_id += 1

        # Sleep Schedule characteristic (write)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_SLEEP_SCHEDULE_UUID,
            value=[],
            notifying=False,
            flags=['write', 'write-without-response'],
            write_callback=self.on_sleep_schedule_write
        )
        char_id += 1

        # Frame Stream characteristic (write)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_FRAME_STREAM_UUID,
            value=[],
            notifying=False,
            flags=['write', 'write-without-response'],
            write_callback=self.on_frame_stream_write
        )
        char_id += 1

        # Pattern List characteristic (read)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_PATTERN_LIST_UUID,
            value=[],
            notifying=False,
            flags=['read'],
            read_callback=self.on_pattern_list_read
        )
        char_id += 1

        # Game List characteristic (read)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_GAME_LIST_UUID,
            value=[],
            notifying=False,
            flags=['read'],
            read_callback=self.on_game_list_read
        )
        char_id += 1

        # Capabilities characteristic (read)
        self.peripheral.add_characteristic(
            srv_id=self.srv_id,
            chr_id=char_id,
            uuid=protocol.CHAR_CAPABILITIES_UUID,
            value=[],
            notifying=False,
            flags=['read'],
            read_callback=self.on_capabilities_read
        )

        logger.info("GATT services and characteristics configured")

    # Characteristic callbacks

    def on_brightness_write(self, value, options):
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
                logger.info("Brightness set successfully")
            else:
                logger.error(f"Failed to set brightness: {response.status_code}")
        except Exception as e:
            logger.error(f"Error setting brightness: {e}")

    def on_pattern_write(self, value, options):
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
                logger.info("Pattern set successfully")
            else:
                logger.error(f"Failed to set pattern: {response.status_code}")
        except Exception as e:
            logger.error(f"Error setting pattern: {e}")

    def on_game_control_write(self, value, options):
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
                    logger.info("Game started successfully")
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
                    logger.info("Game input sent successfully")
                else:
                    logger.error(f"Failed to send game input: {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending game input: {e}")

    def on_power_limit_read(self):
        """Handle power limit read"""
        try:
            response = requests.get(f"{self.api_url}/power-limit", timeout=2)
            if response.status_code == 200:
                data = response.json()
                # Convert amps to 0.1A units (2 bytes, big-endian)
                power_amps = data.get('max_current_amps', 80.0)
                power_units = int(power_amps * 10.0)
                return list(struct.pack('>H', power_units))
            else:
                logger.error(f"Failed to read power limit: {response.status_code}")
                # Return default 80A
                return list(struct.pack('>H', 800))
        except Exception as e:
            logger.error(f"Error reading power limit: {e}")
            # Return default 80A
            return list(struct.pack('>H', 800))

    def on_power_limit_write(self, value, options):
        """Handle power limit write"""
        if len(value) != 2:
            logger.warning("Invalid power limit value length")
            return

        # Power limit in 0.1A units
        power_units = struct.unpack('>H', bytes(value))[0]
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
                logger.info("Power limit set successfully")
            else:
                logger.error(f"Failed to set power limit: {response.status_code}")
        except Exception as e:
            logger.error(f"Error setting power limit: {e}")

    def on_sleep_schedule_write(self, value, options):
        """Handle sleep schedule write"""
        if len(value) != 4:
            logger.warning("Invalid sleep schedule value length")
            return

        off_hour, off_min, on_hour, on_min = value[0], value[1], value[2], value[3]

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
                logger.info("Sleep schedule set successfully")
            else:
                logger.error(f"Failed to set sleep schedule: {response.status_code}")
        except Exception as e:
            logger.error(f"Error setting sleep schedule: {e}")

    def on_frame_stream_write(self, value, options):
        """Handle frame stream write (chunked)"""
        # Check for timeout and reset if needed
        self.frame_assembler.check_timeout()

        # Add chunk
        frame_data = self.frame_assembler.add_chunk(bytes(value))

        if frame_data:
            # Complete frame received, send to display
            logger.info("Sending complete frame to display")

            try:
                response = requests.post(
                    f"{self.api_url}/frame",
                    data=frame_data,
                    headers={'Content-Type': 'application/octet-stream'},
                    timeout=2
                )
                if response.status_code == 200:
                    logger.info("Frame sent successfully")
                else:
                    logger.error(f"Failed to send frame: {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending frame: {e}")

    def on_status_read(self):
        """Handle status read request"""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=2)
            if response.status_code == 200:
                status_json = json.dumps(response.json())
                return list(status_json.encode('utf-8'))
            else:
                logger.error(f"Failed to get status: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return []

    def on_config_read(self):
        """Handle config read request"""
        try:
            response = requests.get(f"{self.api_url}/config", timeout=2)
            if response.status_code == 200:
                config_json = json.dumps(response.json())
                return list(config_json.encode('utf-8'))
            else:
                logger.error(f"Failed to get config: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error getting config: {e}")
            return []

    def on_pattern_list_read(self):
        """Handle pattern list read request"""
        try:
            pattern_list_json = protocol.get_pattern_list_json()
            logger.info(f"Sending pattern list: {len(protocol.PATTERNS)} patterns")
            return list(pattern_list_json.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error getting pattern list: {e}")
            return []

    def on_game_list_read(self):
        """Handle game list read request"""
        try:
            game_list_json = protocol.get_game_list_json()
            logger.info(f"Sending game list: {len(protocol.GAMES)} games")
            return list(game_list_json.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error getting game list: {e}")
            return []

    def on_capabilities_read(self):
        """Handle capabilities read request"""
        try:
            capabilities_json = protocol.get_capabilities_json()
            logger.info("Sending device capabilities")
            return list(capabilities_json.encode('utf-8'))
        except Exception as e:
            logger.error(f"Error getting capabilities: {e}")
            return []

    def start(self):
        """Start the BLE server"""
        logger.info("Starting LED Matrix BLE Server")
        logger.info("Advertising as 'LED Matrix'")

        # Publish (start advertising)
        self.peripheral.publish()

        logger.info("✅ BLE Server started successfully")
        logger.info("Waiting for connections...")


def main():
    """Main entry point"""
    try:
        server = LEDMatrixBLEServer()
        server.start()

        # Keep running
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)


if __name__ == "__main__":
    main()
