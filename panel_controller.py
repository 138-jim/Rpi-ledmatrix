#!/usr/bin/env python3
"""
Panel Controller - Clean ESP32 Multi-Panel Communication Layer

This module provides a standardized interface for controlling multiple LED matrix panels
connected to an ESP32. It handles panel positioning, rotation, and serial communication.

Standard Input Format:
- Accepts a simple 2D array of RGB values
- Automatically maps to configured panel layout
- Handles rotation and positioning transparently
"""

import serial
import time
import json
import sys
from typing import List, Tuple, Dict, Any, Optional
import numpy as np


class Panel:
    """Represents a single LED matrix panel with position and rotation"""
    
    def __init__(self, width: int, height: int, x: int = 0, y: int = 0, rotation: int = 0):
        self.width = width
        self.height = height
        self.x = x  # Position in combined display
        self.y = y
        self.rotation = rotation  # 0, 90, 180, 270 degrees
    
    def get_rotated_dimensions(self) -> Tuple[int, int]:
        """Get panel dimensions after rotation"""
        if self.rotation in [90, 270]:
            return (self.height, self.width)
        return (self.width, self.height)
    
    def rotate_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Apply rotation to coordinates within this panel"""
        if self.rotation == 0:
            return (x, y)
        elif self.rotation == 90:
            return (self.height - 1 - y, x)
        elif self.rotation == 180:
            return (self.width - 1 - x, self.height - 1 - y)
        elif self.rotation == 270:
            return (y, self.width - 1 - x)
        else:
            return (x, y)


class PanelController:
    """
    Main controller for ESP32 multi-panel LED matrix system
    
    Standardized Input Format:
        display_frame(frame) where frame is:
        - 2D numpy array: shape (height, width, 3) with RGB values 0-255
        - OR List of lists: [[r,g,b], [r,g,b], ...] row by row
    """
    
    def __init__(self, port: str = "COM3", baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False
        
        self.panels: List[Panel] = []
        self.total_width = 0
        self.total_height = 0
        self._update_dimensions()
    
    def add_panel(self, width: int, height: int, x: int, y: int, rotation: int = 0) -> Panel:
        """Add a panel to the system"""
        panel = Panel(width, height, x, y, rotation)
        self.panels.append(panel)
        self._update_dimensions()
        return panel
    
    def clear_panels(self):
        """Remove all panels"""
        self.panels.clear()
        self._update_dimensions()
    
    def _update_dimensions(self):
        """Calculate total display dimensions"""
        if not self.panels:
            self.total_width = self.total_height = 0
            return
        
        max_right = max_bottom = 0
        for panel in self.panels:
            rot_width, rot_height = panel.get_rotated_dimensions()
            max_right = max(max_right, panel.x + rot_width)
            max_bottom = max(max_bottom, panel.y + rot_height)
        
        self.total_width = max_right
        self.total_height = max_bottom
    
    def connect(self) -> bool:
        """Connect to ESP32"""
        try:
            print(f"Connecting to ESP32 on {self.port}...")
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=5.0,
                write_timeout=10.0
            )
            
            # Wait for ESP32 boot
            time.sleep(3)
            self.serial_connection.reset_input_buffer()
            
            # Test with INFO command
            self.serial_connection.write(b"INFO\\n")
            self.serial_connection.flush()
            time.sleep(1)
            
            response = ""
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.serial_connection.in_waiting > 0:
                    response += self.serial_connection.read_all().decode('utf-8', errors='ignore')
                time.sleep(0.1)
            
            if "ESP32" in response:
                self.connected = True
                print("✓ ESP32 connected successfully")
                
                # Configure ESP32 for total display size
                if self.total_width > 0 and self.total_height > 0:
                    success = self._configure_esp32(self.total_width, self.total_height)
                    if success:
                        print(f"✓ ESP32 configured for {self.total_width}x{self.total_height} display")
                    else:
                        print("⚠ ESP32 connected but configuration failed")
                
                return True
            else:
                print("✗ No valid ESP32 response")
                return False
                
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from ESP32"""
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
        self.connected = False
        print("Disconnected from ESP32")
    
    def _configure_esp32(self, width: int, height: int) -> bool:
        """Configure ESP32 display dimensions"""
        if not self.connected:
            return False
        
        try:
            # Send CONFIG command
            command = f"CONFIG:{width},{height}\\n"
            self.serial_connection.write(command.encode())
            self.serial_connection.flush()
            
            # Wait for CONFIG_OK response
            start_time = time.time()
            while time.time() - start_time < 10:
                if self.serial_connection.in_waiting > 0:
                    line = self.serial_connection.readline().decode().strip()
                    if "CONFIG_OK" in line:
                        return True
                    elif "CONFIG_ERROR" in line:
                        print(f"ESP32 config error: {line}")
                        return False
                time.sleep(0.1)
            
            print("ESP32 configuration timeout")
            return False
            
        except Exception as e:
            print(f"Configuration error: {e}")
            return False
    
    def display_frame(self, frame) -> bool:
        """
        Display a frame on the LED matrix
        
        Args:
            frame: 2D array of RGB values, shape (height, width, 3)
                  Can be numpy array or list of lists: [[r,g,b], [r,g,b], ...]
        
        Returns:
            bool: True if frame was sent successfully
        """
        if not self.connected or not self.panels:
            return False
        
        # Convert input to numpy array for easier handling
        if isinstance(frame, list):
            frame = np.array(frame, dtype=np.uint8)
        elif not isinstance(frame, np.ndarray):
            print("Error: Frame must be numpy array or list")
            return False
        
        # Validate frame dimensions
        if len(frame.shape) != 3 or frame.shape[2] != 3:
            print(f"Error: Frame must be shape (height, width, 3), got {frame.shape}")
            return False
        
        frame_height, frame_width = frame.shape[:2]
        
        # Create combined frame for ESP32 (total display size)
        combined_frame = np.zeros((self.total_height, self.total_width, 3), dtype=np.uint8)
        
        # Map input frame to panels with rotation
        for panel in self.panels:
            rot_width, rot_height = panel.get_rotated_dimensions()
            
            # Extract the section of input frame that corresponds to this panel
            for panel_y in range(min(rot_height, frame_height - panel.y)):
                for panel_x in range(min(rot_width, frame_width - panel.x)):
                    
                    # Get pixel from input frame
                    input_y = panel.y + panel_y
                    input_x = panel.x + panel_x
                    
                    if (input_x < frame_width and input_y < frame_height and
                        input_x >= 0 and input_y >= 0):
                        
                        # Apply rotation to determine where this pixel goes in the panel
                        rotated_x, rotated_y = panel.rotate_coordinates(panel_x, panel_y)
                        
                        # Map to combined frame (ESP32 coordinates)
                        combined_x = panel.x + rotated_x
                        combined_y = panel.y + rotated_y
                        
                        if (combined_x < self.total_width and combined_y < self.total_height):
                            combined_frame[combined_y, combined_x] = frame[input_y, input_x]
        
        # Send to ESP32
        return self._send_frame_to_esp32(combined_frame)
    
    def _send_frame_to_esp32(self, frame: np.ndarray) -> bool:
        """Send frame data to ESP32"""
        try:
            # Convert to RGB bytes in row-major order
            rgb_data = frame.flatten().tobytes()
            data_size = len(rgb_data)
            
            # Clear input buffer
            self.serial_connection.reset_input_buffer()
            
            # Send frame command: FRAME:size:<data>:END
            header = f"FRAME:{data_size}:"
            self.serial_connection.write(header.encode())
            self.serial_connection.flush()
            time.sleep(0.01)
            
            # Send binary data
            self.serial_connection.write(rgb_data)
            self.serial_connection.flush()
            time.sleep(0.01)
            
            # Send end marker
            self.serial_connection.write(b":END")
            self.serial_connection.flush()
            
            # Wait for acknowledgment
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode().strip()
                    if response == "FRAME_OK":
                        return True
                    elif "FRAME_ERROR" in response:
                        print(f"ESP32 frame error: {response}")
                        return False
                time.sleep(0.01)
            
            print("Frame send timeout")
            return False
            
        except Exception as e:
            print(f"Frame send error: {e}")
            return False
    
    def clear_display(self) -> bool:
        """Clear the display"""
        if not self.connected:
            return False
        
        try:
            self.serial_connection.write(b"CLEAR\\n")
            self.serial_connection.flush()
            
            start_time = time.time()
            while time.time() - start_time < 3:
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode().strip()
                    return response == "CLEAR_OK"
                time.sleep(0.01)
            return False
            
        except Exception as e:
            print(f"Clear error: {e}")
            return False
    
    def set_brightness(self, brightness: int) -> bool:
        """Set LED brightness (0-255)"""
        if not self.connected or not (0 <= brightness <= 255):
            return False
        
        try:
            command = f"BRIGHTNESS:{brightness}\\n"
            self.serial_connection.write(command.encode())
            self.serial_connection.flush()
            
            start_time = time.time()
            while time.time() - start_time < 3:
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode().strip()
                    return response == "BRIGHTNESS_OK"
                time.sleep(0.01)
            return False
            
        except Exception as e:
            print(f"Brightness error: {e}")
            return False
    
    def get_status(self) -> Optional[str]:
        """Get ESP32 status"""
        if not self.connected:
            return None
        
        try:
            self.serial_connection.write(b"STATUS\\n")
            self.serial_connection.flush()
            
            start_time = time.time()
            while time.time() - start_time < 3:
                if self.serial_connection.in_waiting > 0:
                    response = self.serial_connection.readline().decode().strip()
                    if "STATUS:" in response:
                        return response
                time.sleep(0.01)
            return None
            
        except Exception as e:
            print(f"Status error: {e}")
            return None
    
    def save_config(self, filename: str):
        """Save panel configuration to JSON file"""
        config = {
            "panels": [
                {
                    "width": p.width,
                    "height": p.height, 
                    "x": p.x,
                    "y": p.y,
                    "rotation": p.rotation
                }
                for p in self.panels
            ],
            "total_width": self.total_width,
            "total_height": self.total_height
        }
        
        with open(filename, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Configuration saved to {filename}")
    
    def load_config(self, filename: str):
        """Load panel configuration from JSON file"""
        with open(filename, 'r') as f:
            config = json.load(f)
        
        self.clear_panels()
        for panel_config in config["panels"]:
            self.add_panel(
                width=panel_config["width"],
                height=panel_config["height"],
                x=panel_config["x"], 
                y=panel_config["y"],
                rotation=panel_config["rotation"]
            )
        
        print(f"Configuration loaded from {filename}")
        print(f"Total display: {self.total_width}x{self.total_height}")


def create_default_2x2_layout() -> PanelController:
    """Create a controller with default 2x2 layout of 16x16 panels"""
    controller = PanelController()
    
    # Add four 16x16 panels in 2x2 grid
    controller.add_panel(16, 16, 0, 0, 0)    # Top-left
    controller.add_panel(16, 16, 16, 0, 0)   # Top-right  
    controller.add_panel(16, 16, 0, 16, 0)   # Bottom-left
    controller.add_panel(16, 16, 16, 16, 0)  # Bottom-right
    
    return controller


def create_test_frame(width: int, height: int, pattern: str = "gradient") -> np.ndarray:
    """Create test frames for debugging"""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    if pattern == "gradient":
        for y in range(height):
            for x in range(width):
                frame[y, x] = [x * 255 // width, y * 255 // height, 128]
    
    elif pattern == "corners":
        # Red corners to test panel positioning
        frame[0, 0] = [255, 0, 0]  # Top-left red
        frame[0, width-1] = [0, 255, 0]  # Top-right green
        frame[height-1, 0] = [0, 0, 255]  # Bottom-left blue
        frame[height-1, width-1] = [255, 255, 0]  # Bottom-right yellow
    
    elif pattern == "cross":
        # White cross in center
        mid_x, mid_y = width // 2, height // 2
        frame[mid_y, :] = [255, 255, 255]  # Horizontal line
        frame[:, mid_x] = [255, 255, 255]  # Vertical line
    
    return frame


def main():
    """Example usage and test"""
    print("Panel Controller Test")
    print("=" * 40)
    
    # Create controller with default 2x2 layout
    controller = create_default_2x2_layout()
    
    # Show configuration
    print(f"Panels configured: {len(controller.panels)}")
    print(f"Total display: {controller.total_width}x{controller.total_height}")
    
    # Connect to ESP32
    port = "COM3" if sys.platform.startswith('win') else "/dev/ttyUSB0"
    controller.port = port
    
    if controller.connect():
        print("\\nTesting display patterns...")
        
        # Test 1: Corner markers
        print("1. Corner test pattern")
        frame = create_test_frame(32, 32, "corners") 
        controller.display_frame(frame)
        time.sleep(3)
        
        # Test 2: Cross pattern
        print("2. Cross test pattern")
        frame = create_test_frame(32, 32, "cross")
        controller.display_frame(frame)
        time.sleep(3)
        
        # Test 3: Gradient
        print("3. Gradient test pattern")
        frame = create_test_frame(32, 32, "gradient")
        controller.display_frame(frame)
        time.sleep(3)
        
        # Clear
        controller.clear_display()
        controller.disconnect()
    else:
        print("Connection failed - run in test mode")
        
        # Save default config for later use
        controller.save_config("default_2x2.json")


if __name__ == "__main__":
    main()