#!/usr/bin/env python3
"""
WS2812B LED Panel Controller for ESP32
Supports multiple panels with individual rotation settings
Compatible with Windows and Linux
"""

import numpy as np
import serial
import serial.tools.list_ports
import struct
import time
import json
from typing import List, Tuple, Optional
from enum import Enum
import threading
import queue
from abc import ABC, abstractmethod


class Rotation(Enum):
    """Panel rotation angles"""
    NONE = 0
    CW_90 = 90
    CW_180 = 180
    CW_270 = 270


class Panel:
    """Represents a single LED panel"""
    
    def __init__(self, panel_id: int, width: int = 16, height: int = 16, 
                 rotation: Rotation = Rotation.NONE, 
                 position: Tuple[int, int] = (0, 0)):
        self.id = panel_id
        self.width = width
        self.height = height
        self.rotation = rotation
        self.position = position  # (x, y) position in the grid
        self.pixels = np.zeros((height, width, 3), dtype=np.uint8)
        
    def rotate_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Rotate coordinates based on panel rotation"""
        if self.rotation == Rotation.NONE:
            return x, y
        elif self.rotation == Rotation.CW_90:
            return self.height - 1 - y, x
        elif self.rotation == Rotation.CW_180:
            return self.width - 1 - x, self.height - 1 - y
        elif self.rotation == Rotation.CW_270:
            return y, self.width - 1 - x
            
    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """Set a pixel with rotation applied"""
        if 0 <= x < self.width and 0 <= y < self.height:
            rx, ry = self.rotate_coordinates(x, y)
            self.pixels[ry, rx] = color
            
    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get a pixel with rotation applied"""
        if 0 <= x < self.width and 0 <= y < self.height:
            rx, ry = self.rotate_coordinates(x, y)
            return tuple(self.pixels[ry, rx])
        return (0, 0, 0)
    
    def clear(self):
        """Clear all pixels"""
        self.pixels.fill(0)
        
    def get_flat_array(self) -> np.ndarray:
        """Get flattened array for serial transmission"""
        return self.pixels.flatten()


class PanelGrid:
    """Manages a grid of LED panels"""
    
    def __init__(self, grid_width: int = 2, grid_height: int = 2, 
                 panel_width: int = 16, panel_height: int = 16,
                 wiring_pattern: str = "sequential"):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.panel_width = panel_width
        self.panel_height = panel_height
        self.total_width = grid_width * panel_width
        self.total_height = grid_height * panel_height
        self.wiring_pattern = wiring_pattern  # "sequential", "snake", "vertical_snake"
        self.panels: List[Panel] = []
        
        # Create panels based on wiring pattern
        self._create_panels()
                
    def _create_panels(self):
        """Create panels based on wiring pattern"""
        panel_id = 0
        
        if self.wiring_pattern == "snake":
            # Snake/zigzag pattern (common for daisy-chained panels)
            # Goes left-to-right, then right-to-left, alternating
            for gy in range(self.grid_height):
                if gy % 2 == 0:  # Even rows: left to right
                    for gx in range(self.grid_width):
                        panel = Panel(
                            panel_id=panel_id,
                            width=self.panel_width,
                            height=self.panel_height,
                            position=(gx, gy)
                        )
                        self.panels.append(panel)
                        panel_id += 1
                else:  # Odd rows: right to left
                    for gx in range(self.grid_width - 1, -1, -1):
                        panel = Panel(
                            panel_id=panel_id,
                            width=self.panel_width,
                            height=self.panel_height,
                            position=(gx, gy)
                        )
                        self.panels.append(panel)
                        panel_id += 1
                        
        elif self.wiring_pattern == "vertical_snake":
            # Vertical snake pattern
            # Goes top-to-bottom, then bottom-to-top, alternating
            for gx in range(self.grid_width):
                if gx % 2 == 0:  # Even columns: top to bottom
                    for gy in range(self.grid_height):
                        panel = Panel(
                            panel_id=panel_id,
                            width=self.panel_width,
                            height=self.panel_height,
                            position=(gx, gy)
                        )
                        self.panels.append(panel)
                        panel_id += 1
                else:  # Odd columns: bottom to top
                    for gy in range(self.grid_height - 1, -1, -1):
                        panel = Panel(
                            panel_id=panel_id,
                            width=self.panel_width,
                            height=self.panel_height,
                            position=(gx, gy)
                        )
                        self.panels.append(panel)
                        panel_id += 1
                        
        else:  # sequential (default)
            # Sequential pattern: left to right, top to bottom
            for gy in range(self.grid_height):
                for gx in range(self.grid_width):
                    panel = Panel(
                        panel_id=panel_id,
                        width=self.panel_width,
                        height=self.panel_height,
                        position=(gx, gy)
                    )
                    self.panels.append(panel)
                    panel_id += 1
                    
    def get_panel_at_position(self, grid_x: int, grid_y: int) -> Optional[Panel]:
        """Get panel at specific grid position"""
        for panel in self.panels:
            if panel.position == (grid_x, grid_y):
                return panel
        return None
                
    def set_panel_rotation(self, panel_id: int, rotation: Rotation):
        """Set rotation for a specific panel"""
        if 0 <= panel_id < len(self.panels):
            self.panels[panel_id].rotation = rotation
            
    def set_pixel(self, x: int, y: int, color: Tuple[int, int, int]):
        """Set a pixel in the overall grid"""
        if 0 <= x < self.total_width and 0 <= y < self.total_height:
            # Find which panel this pixel belongs to
            panel_x = x // self.panel_width
            panel_y = y // self.panel_height
            
            # Get the panel at this grid position
            panel = self.get_panel_at_position(panel_x, panel_y)
            
            if panel:
                # Calculate pixel position within the panel
                local_x = x % self.panel_width
                local_y = y % self.panel_height
                panel.set_pixel(local_x, local_y, color)
                
    def clear(self):
        """Clear all panels"""
        for panel in self.panels:
            panel.clear()
            
    def get_display_buffer(self) -> np.ndarray:
        """Get the complete display buffer for transmission"""
        # Concatenate all panel data in order
        buffers = [panel.get_flat_array() for panel in self.panels]
        return np.concatenate(buffers)


class SerialProtocol:
    """Handles serial communication protocol with ESP32"""
    
    # Protocol commands
    CMD_SET_PIXELS = 0x01
    CMD_CLEAR = 0x02
    CMD_BRIGHTNESS = 0x03
    CMD_SHOW = 0x04
    CMD_CONFIG = 0x05
    
    @staticmethod
    def create_packet(command: int, data: bytes = b'') -> bytes:
        """Create a packet with header and checksum"""
        packet = bytearray()
        packet.append(0xAA)  # Start byte
        packet.append(0x55)  # Start byte 2
        packet.append(command)
        
        # Data length in little-endian format
        data_len = len(data)
        packet.append(data_len & 0xFF)  # Low byte
        packet.append((data_len >> 8) & 0xFF)  # High byte
        
        # Add data if present
        if data:
            packet.extend(data)
        
        # Calculate checksum (sum of all bytes after start bytes)
        checksum = 0
        for byte in packet[2:]:  # Skip the two start bytes
            checksum = (checksum + byte) & 0xFF
        packet.append(checksum)
        
        return bytes(packet)


class ESP32Controller:
    """Main controller for ESP32 communication"""
    
    def __init__(self, port: Optional[str] = None, baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate  # Changed from 921600 to 115200
        self.serial_conn = None
        self.send_queue = queue.Queue()
        self.send_thread = None
        self.running = False
        
    def find_esp32_port(self) -> Optional[str]:
        """Auto-detect ESP32 port"""
        ports = serial.tools.list_ports.comports()
        for port in ports:
            # Check for common ESP32 identifiers
            if 'CH340' in port.description or 'CP210' in port.description or \
               'USB Serial' in port.description or 'ESP32' in port.description:
                return port.device
        return None
        
    def connect(self) -> bool:
        """Connect to ESP32"""
        if not self.port:
            self.port = self.find_esp32_port()
            if not self.port:
                print("ESP32 not found. Please specify port manually.")
                return False
                
        try:
            self.serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1.0,
                write_timeout=2.0  # Added write timeout
            )
            
            # Clear buffers
            self.serial_conn.reset_input_buffer()
            self.serial_conn.reset_output_buffer()
            
            time.sleep(2)  # Wait for ESP32 to reset
            
            # Read and print any startup messages
            print("Reading ESP32 startup messages...")
            start_time = time.time()
            while time.time() - start_time < 1:
                if self.serial_conn.in_waiting:
                    msg = self.serial_conn.readline().decode('utf-8', errors='ignore').strip()
                    if msg:
                        print(f"ESP32: {msg}")
            
            self.running = True
            self.send_thread = threading.Thread(target=self._send_worker)
            self.send_thread.start()
            
            print(f"Connected to ESP32 on {self.port} at {self.baudrate} baud")
            return True
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from ESP32"""
        self.running = False
        if self.send_thread:
            self.send_thread.join()
        if self.serial_conn:
            self.serial_conn.close()
            
    def _send_worker(self):
        """Worker thread for sending data"""
        while self.running:
            try:
                packet = self.send_queue.get(timeout=0.1)
                if self.serial_conn:
                    self.serial_conn.write(packet)
                    self.serial_conn.flush()  # Force send immediately
                    
                    # Small delay between packets to avoid overwhelming ESP32
                    time.sleep(0.001)
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Send error: {e}")
                
    def send_pixels(self, pixel_data: np.ndarray):
        """Send pixel data to ESP32"""
        # Split data into chunks if necessary (ESP32 has limited buffer)
        chunk_size = 1024  # Smaller chunks for reliability
        data_bytes = pixel_data.tobytes()
        
        print(f"Sending {len(data_bytes)} bytes in chunks of {chunk_size}")
        
        for i in range(0, len(data_bytes), chunk_size):
            chunk = data_bytes[i:i+chunk_size]
            packet = SerialProtocol.create_packet(
                SerialProtocol.CMD_SET_PIXELS, 
                struct.pack('<H', i) + chunk
            )
            self.send_queue.put(packet)
            
            # Add small delay between chunks to avoid buffer overflow
            time.sleep(0.01)
            
        # Send show command
        self.send_queue.put(
            SerialProtocol.create_packet(SerialProtocol.CMD_SHOW)
        )
        
        # Wait for queue to empty
        while not self.send_queue.empty():
            time.sleep(0.01)
        
    def set_brightness(self, brightness: int):
        """Set global brightness (0-255)"""
        brightness = max(0, min(255, brightness))  # Clamp to valid range
        packet = SerialProtocol.create_packet(
            SerialProtocol.CMD_BRIGHTNESS,
            bytes([brightness])
        )
        self.send_queue.put(packet)
        print(f"Setting brightness to {brightness}")
        
    def clear_display(self):
        """Clear all LEDs"""
        packet = SerialProtocol.create_packet(SerialProtocol.CMD_CLEAR)
        self.send_queue.put(packet)
        
    def configure_panels(self, num_panels: int, leds_per_panel: int):
        """Configure panel settings on ESP32"""
        # Pack as little-endian 16-bit values
        data = bytearray()
        data.append(num_panels & 0xFF)  # Low byte
        data.append((num_panels >> 8) & 0xFF)  # High byte
        data.append(leds_per_panel & 0xFF)  # Low byte
        data.append((leds_per_panel >> 8) & 0xFF)  # High byte
        
        packet = SerialProtocol.create_packet(SerialProtocol.CMD_CONFIG, bytes(data))
        self.send_queue.put(packet)
        
        print(f"Configuring: {num_panels} panels, {leds_per_panel} LEDs per panel")


class Animation(ABC):
    """Base class for animations"""
    
    @abstractmethod
    def update(self, grid: PanelGrid, frame: int):
        """Update animation for current frame"""
        pass


class RainbowAnimation(Animation):
    """Rainbow wave animation"""
    
    def update(self, grid: PanelGrid, frame: int):
        for y in range(grid.total_height):
            for x in range(grid.total_width):
                hue = (x + y + frame) % 360
                color = self.hsv_to_rgb(hue / 360.0, 1.0, 1.0)
                grid.set_pixel(x, y, color)
                
    @staticmethod
    def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB"""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return int(r * 255), int(g * 255), int(b * 255)


class LEDDisplay:
    """High-level LED display controller"""
    
    def __init__(self, config_file: Optional[str] = None):
        # Default configuration for 16x16 panels
        self.grid_config = {
            'grid_width': 2,      # 2x2 for 32x32 display
            'grid_height': 2,     # Can be 4x16 for larger display
            'panel_width': 16,    # 16x16 panels
            'panel_height': 16,
            'wiring_pattern': 'snake'  # Common for daisy-chained panels
        }
        
        # Load config if provided
        if config_file:
            self.load_config(config_file)
            
        # Create grid with configuration
        self.grid = PanelGrid(
            grid_width=self.grid_config['grid_width'],
            grid_height=self.grid_config['grid_height'],
            panel_width=self.grid_config['panel_width'],
            panel_height=self.grid_config['panel_height'],
            wiring_pattern=self.grid_config['wiring_pattern']
        )
        
        self.controller = ESP32Controller()
        self.animation = None
        self.frame_rate = 30
        self.running = False
            
    def load_config(self, filename: str):
        """Load panel configuration from JSON file"""
        try:
            with open(filename, 'r') as f:
                config = json.load(f)
                
            # Load grid configuration
            if 'grid' in config:
                self.grid_config.update(config['grid'])
                
            # Recreate grid if dimensions changed
            if hasattr(self, 'grid'):
                self.grid = PanelGrid(
                    grid_width=self.grid_config['grid_width'],
                    grid_height=self.grid_config['grid_height'],
                    panel_width=self.grid_config['panel_width'],
                    panel_height=self.grid_config['panel_height'],
                    wiring_pattern=self.grid_config['wiring_pattern']
                )
                
            # Apply panel rotations
            for panel_config in config.get('panels', []):
                panel_id = panel_config['id']
                rotation = Rotation(panel_config.get('rotation', 0))
                self.grid.set_panel_rotation(panel_id, rotation)
                
            # Apply other settings
            if 'brightness' in config:
                self.controller.set_brightness(config['brightness'])
                
            if 'frame_rate' in config:
                self.frame_rate = config['frame_rate']
                
        except Exception as e:
            print(f"Failed to load config: {e}")
            
    def save_config(self, filename: str):
        """Save panel configuration to JSON file"""
        config = {
            'grid': self.grid_config,
            'frame_rate': self.frame_rate,
            'panels': [
                {
                    'id': panel.id,
                    'rotation': panel.rotation.value,
                    'position': panel.position
                }
                for panel in self.grid.panels
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
            
    def connect(self) -> bool:
        """Connect to ESP32"""
        if self.controller.connect():
            # Configure panels on ESP32
            total_leds = self.grid.panel_width * self.grid.panel_height
            self.controller.configure_panels(len(self.grid.panels), total_leds)
            return True
        return False
        
    def disconnect(self):
        """Disconnect from ESP32"""
        self.running = False
        self.controller.disconnect()
        
    def display_frame(self):
        """Send current frame to display"""
        buffer = self.grid.get_display_buffer()
        self.controller.send_pixels(buffer)
        
    def run_animation(self, animation: Animation):
        """Run an animation loop"""
        self.animation = animation
        self.running = True
        frame = 0
        
        while self.running:
            start_time = time.time()
            
            # Update animation
            self.animation.update(self.grid, frame)
            
            # Send to display
            self.display_frame()
            
            # Frame rate control
            elapsed = time.time() - start_time
            sleep_time = max(0, (1.0 / self.frame_rate) - elapsed)
            time.sleep(sleep_time)
            
            frame += 1
            
    def test_panels(self):
        """Test each panel individually"""
        print("Testing panels...")
        for i, panel in enumerate(self.grid.panels):
            print(f"Testing panel {i} at position {panel.position}")
            self.grid.clear()
            # Light up panel in white
            for y in range(panel.height):
                for x in range(panel.width):
                    panel.set_pixel(x, y, (255, 255, 255))
            self.display_frame()
            time.sleep(0.5)
        self.grid.clear()
        self.display_frame()
        print("Panel test complete")
        
    def test_communication(self):
        """Test basic communication with ESP32"""
        print("Testing communication...")
        
        # Test 1: Clear command
        print("Test 1: Sending clear command")
        packet = SerialProtocol.create_packet(SerialProtocol.CMD_CLEAR)
        self.controller.send_queue.put(packet)
        time.sleep(0.5)
        
        # Test 2: Brightness command
        print("Test 2: Setting brightness to 64")
        packet = SerialProtocol.create_packet(
            SerialProtocol.CMD_BRIGHTNESS,
            bytes([64])
        )
        self.controller.send_queue.put(packet)
        time.sleep(0.5)
        
        # Test 3: Simple pixel data
        print("Test 3: Sending red pixels")
        test_data = np.full((10, 3), [255, 0, 0], dtype=np.uint8)  # 10 red pixels
        packet = SerialProtocol.create_packet(
            SerialProtocol.CMD_SET_PIXELS,
            struct.pack('<H', 0) + test_data.tobytes()
        )
        self.controller.send_queue.put(packet)
        time.sleep(0.5)
        
        # Show command
        packet = SerialProtocol.create_packet(SerialProtocol.CMD_SHOW)
        self.controller.send_queue.put(packet)
        time.sleep(0.5)
        
        print("Communication test complete")


# Example usage
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='WS2812B LED Panel Controller')
    parser.add_argument('--port', type=str, help='Serial port (auto-detect if not specified)')
    parser.add_argument('--config', type=str, default='panel_config.json', help='Configuration file')
    parser.add_argument('--pattern', type=str, default='snake', 
                       choices=['sequential', 'snake', 'vertical_snake'],
                       help='Panel wiring pattern')
    parser.add_argument('--test', action='store_true', help='Run test pattern')
    parser.add_argument('--demo', action='store_true', help='Run demo animations')
    
    args = parser.parse_args()
    
    # Create display controller
    display = LEDDisplay()
    
    # Override wiring pattern if specified
    if args.pattern:
        display.grid_config['wiring_pattern'] = args.pattern
        display.grid = PanelGrid(
            grid_width=display.grid_config['grid_width'],
            grid_height=display.grid_config['grid_height'],
            panel_width=display.grid_config['panel_width'],
            panel_height=display.grid_config['panel_height'],
            wiring_pattern=args.pattern
        )
    
    # Example: Set up panel rotations for proper orientation
    # This depends on how your panels are physically mounted
    # For a 2x2 grid with snake wiring (common for 32x32 display):
    if display.grid_config['wiring_pattern'] == 'snake':
        # Panels in odd rows might need 180° rotation
        for panel in display.grid.panels:
            gx, gy = panel.position
            if gy % 2 == 1:  # Odd rows
                display.grid.set_panel_rotation(panel.id, Rotation.CW_180)
    
    # Save configuration
    display.save_config(args.config)
    
    # Set specific port if provided
    if args.port:
        display.controller.port = args.port
    
    # Connect to ESP32
    if display.connect():
        try:
            if args.test:
                # Test each panel individually
                print("Testing panels individually...")
                display.test_panels()
                
                # Test pattern to verify wiring
                print("Testing wiring pattern...")
                for i in range(100):
                    display.grid.clear()
                    # Light up panels in sequence
                    panel_idx = i % len(display.grid.panels)
                    panel = display.grid.panels[panel_idx]
                    for y in range(panel.height):
                        for x in range(panel.width):
                            panel.set_pixel(x, y, (255, 0, 0))
                    display.display_frame()
                    time.sleep(0.1)
                    
            elif args.demo:
                # Run demo animations
                print("Running demo animations...")
                print("Press Ctrl+C to stop")
                
                animations = [
                    RainbowAnimation(),
                    # Add more animations here
                ]
                
                for animation in animations:
                    print(f"Running {animation.__class__.__name__}...")
                    display.animation = animation
                    
                    # Run for 10 seconds
                    start_time = time.time()
                    frame = 0
                    while time.time() - start_time < 10:
                        animation.update(display.grid, frame)
                        display.display_frame()
                        time.sleep(1.0 / display.frame_rate)
                        frame += 1
                        
            else:
                # Run rainbow animation
                print("Running rainbow animation...")
                print("Press Ctrl+C to stop")
                animation = RainbowAnimation()
                display.run_animation(animation)
            
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            display.grid.clear()
            display.display_frame()
            display.disconnect()
    else:
        print("Failed to connect to ESP32")
        print("Check that:")
        print("1. ESP32 is connected via USB")
        print("2. Correct drivers are installed")
        print("3. Firmware is uploaded to ESP32")
        print(f"4. Try specifying port manually: python {__file__} --port COM3")