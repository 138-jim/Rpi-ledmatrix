#!/usr/bin/env python3
"""
LED Matrix Controller for Raspberry Pi
Renders text, patterns, and animations then sends frames to ESP32
"""

import serial
import time
import math
import threading
import colorsys
from typing import Tuple, List, Optional
from PIL import Image, ImageDraw, ImageFont
import numpy as np


class LEDMatrix:
    def __init__(self, width: int = 16, height: int = 16):
        self.width = width
        self.height = height
        self.buffer = np.zeros((height, width, 3), dtype=np.uint8)
    
    def clear(self):
        """Clear the matrix buffer"""
        self.buffer.fill(0)
    
    def set_pixel(self, x: int, y: int, r: int, g: int, b: int):
        """Set a single pixel color"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y, x] = [r, g, b]
    
    def get_pixel(self, x: int, y: int) -> Tuple[int, int, int]:
        """Get a single pixel color"""
        if 0 <= x < self.width and 0 <= y < self.height:
            return tuple(self.buffer[y, x])
        return (0, 0, 0)
    
    def fill(self, r: int, g: int, b: int):
        """Fill entire matrix with color"""
        self.buffer[:, :] = [r, g, b]
    
    def draw_text(self, text: str, x: int, y: int, color: Tuple[int, int, int]):
        """Draw text using built-in 5x7 font"""
        font_5x7 = self._get_font_5x7()
        current_x = x
        
        for char in text:
            if char in font_5x7:
                char_data = font_5x7[char]
                for col in range(5):
                    for row in range(7):
                        if char_data[col] & (1 << row):
                            self.set_pixel(current_x + col, y + row, *color)
                current_x += 6  # 5 pixels + 1 spacing
    
    def get_text_width(self, text: str) -> int:
        """Get text width in pixels"""
        return len(text) * 6 - 1
    
    def _get_font_5x7(self) -> dict:
        """5x7 font definition"""
        return {
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
            '"': [0x00, 0x07, 0x00, 0x07, 0x00],
            '#': [0x14, 0x7F, 0x14, 0x7F, 0x14],
            '$': [0x24, 0x2A, 0x7F, 0x2A, 0x12],
            '%': [0x23, 0x13, 0x08, 0x64, 0x62],
            '&': [0x36, 0x49, 0x56, 0x20, 0x50],
            "'": [0x00, 0x08, 0x07, 0x03, 0x00],
            '(': [0x00, 0x1C, 0x22, 0x41, 0x00],
            ')': [0x00, 0x41, 0x22, 0x1C, 0x00],
            '*': [0x2A, 0x1C, 0x7F, 0x1C, 0x2A],
            '+': [0x08, 0x08, 0x3E, 0x08, 0x08],
            ',': [0x00, 0x80, 0x70, 0x30, 0x00],
            '-': [0x08, 0x08, 0x08, 0x08, 0x08],
            '.': [0x00, 0x00, 0x60, 0x60, 0x00],
            '/': [0x20, 0x10, 0x08, 0x04, 0x02],
            '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
            '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
            '2': [0x72, 0x49, 0x49, 0x49, 0x46],
            '3': [0x21, 0x41, 0x49, 0x4D, 0x33],
            '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
            '5': [0x27, 0x45, 0x45, 0x45, 0x39],
            '6': [0x3C, 0x4A, 0x49, 0x49, 0x31],
            '7': [0x41, 0x21, 0x11, 0x09, 0x07],
            '8': [0x36, 0x49, 0x49, 0x49, 0x36],
            '9': [0x46, 0x49, 0x49, 0x29, 0x1E],
            ':': [0x00, 0x00, 0x14, 0x00, 0x00],
            ';': [0x00, 0x40, 0x34, 0x00, 0x00],
            '<': [0x00, 0x08, 0x14, 0x22, 0x41],
            '=': [0x14, 0x14, 0x14, 0x14, 0x14],
            '>': [0x00, 0x41, 0x22, 0x14, 0x08],
            '?': [0x02, 0x01, 0x59, 0x09, 0x06],
            '@': [0x3E, 0x41, 0x5D, 0x59, 0x4E],
            'A': [0x7C, 0x12, 0x11, 0x12, 0x7C],
            'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
            'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
            'D': [0x7F, 0x41, 0x41, 0x41, 0x3E],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
            'F': [0x7F, 0x09, 0x09, 0x09, 0x01],
            'G': [0x3E, 0x41, 0x41, 0x51, 0x73],
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
            'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
            'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
            'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
            'M': [0x7F, 0x02, 0x1C, 0x02, 0x7F],
            'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
            'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
            'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
            'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
            'S': [0x26, 0x49, 0x49, 0x49, 0x32],
            'T': [0x03, 0x01, 0x7F, 0x01, 0x03],
            'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
            'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
            'W': [0x3F, 0x40, 0x38, 0x40, 0x3F],
            'X': [0x63, 0x14, 0x08, 0x14, 0x63],
            'Y': [0x03, 0x04, 0x78, 0x04, 0x03],
            'Z': [0x61, 0x59, 0x49, 0x4D, 0x43],
        }


class PatternGenerator:
    @staticmethod
    def rainbow(matrix: LEDMatrix, offset: float = 0):
        """Generate rainbow pattern"""
        for y in range(matrix.height):
            for x in range(matrix.width):
                hue = (x + y + offset) / (matrix.width + matrix.height)
                r, g, b = colorsys.hsv_to_rgb(hue % 1.0, 1.0, 1.0)
                matrix.set_pixel(x, y, int(r * 255), int(g * 255), int(b * 255))
    
    @staticmethod
    def spiral(matrix: LEDMatrix, offset: float = 0):
        """Generate spiral pattern"""
        center_x, center_y = matrix.width // 2, matrix.height // 2
        for y in range(matrix.height):
            for x in range(matrix.width):
                dx, dy = x - center_x, y - center_y
                angle = math.atan2(dy, dx) + offset
                distance = math.sqrt(dx*dx + dy*dy)
                hue = (angle + distance * 0.1) / (2 * math.pi)
                r, g, b = colorsys.hsv_to_rgb(hue % 1.0, 1.0, 1.0)
                matrix.set_pixel(x, y, int(r * 255), int(g * 255), int(b * 255))
    
    @staticmethod
    def wave(matrix: LEDMatrix, offset: float = 0):
        """Generate wave pattern"""
        for y in range(matrix.height):
            for x in range(matrix.width):
                wave1 = math.sin((x + offset) * 0.5) * 0.5 + 0.5
                wave2 = math.sin((y + offset) * 0.3) * 0.5 + 0.5
                intensity = (wave1 + wave2) / 2
                matrix.set_pixel(x, y, int(intensity * 255), int(intensity * 128), int(intensity * 64))


class ESP32Controller:
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200):
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to ESP32"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2
            )
            self.connected = True
            print(f"Connected to ESP32 on {self.port}")
            time.sleep(2)
            return True
        except serial.SerialException as e:
            print(f"Failed to connect: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from ESP32"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.connected = False
    
    def send_frame(self, matrix: LEDMatrix) -> bool:
        """Send frame data to ESP32"""
        if not self.connected:
            return False
        
        try:
            # Flatten RGB data
            frame_data = matrix.buffer.flatten().tobytes()
            
            # Send frame with protocol
            command = b"FRAME:" + frame_data + b":END"
            self.serial_connection.write(command)
            self.serial_connection.flush()
            
            # Wait for acknowledgment
            response = self.serial_connection.readline().decode().strip()
            return response == "FRAME_OK"
            
        except Exception as e:
            print(f"Error sending frame: {e}")
            return False
    
    def set_brightness(self, brightness: int) -> bool:
        """Set LED brightness"""
        if not self.connected:
            return False
        
        try:
            command = f"BRIGHTNESS:{brightness}\n"
            self.serial_connection.write(command.encode())
            response = self.serial_connection.readline().decode().strip()
            return response == "BRIGHTNESS_OK"
        except Exception as e:
            print(f"Error setting brightness: {e}")
            return False
    
    def clear_display(self) -> bool:
        """Clear display"""
        if not self.connected:
            return False
        
        try:
            self.serial_connection.write(b"CLEAR\n")
            response = self.serial_connection.readline().decode().strip()
            return response == "CLEAR_OK"
        except Exception as e:
            print(f"Error clearing display: {e}")
            return False


class ScrollingText:
    def __init__(self, text: str, matrix: LEDMatrix, color: Tuple[int, int, int] = (255, 0, 0)):
        self.text = text
        self.matrix = matrix
        self.color = color
        self.position = matrix.width
        self.text_width = matrix.get_text_width(text)
    
    def update(self):
        """Update scroll position and render text"""
        self.matrix.clear()
        self.matrix.draw_text(self.text, self.position, 0, self.color)
        
        self.position -= 1
        if self.position < -self.text_width:
            self.position = self.matrix.width
    
    def set_text(self, new_text: str):
        """Change the scrolling text"""
        self.text = new_text
        self.text_width = self.matrix.get_text_width(new_text)
        self.position = self.matrix.width


def main():
    print("LED Matrix Controller")
    print("=" * 30)
    
    # Initialize components
    matrix = LEDMatrix(16, 16)
    controller = ESP32Controller()
    
    # Connect to ESP32
    if not controller.connect():
        print("Failed to connect to ESP32")
        return
    
    # Initialize scrolling text
    scroller = ScrollingText("HELLO WORLD!", matrix, (255, 0, 0))
    pattern_mode = False
    pattern_offset = 0
    current_pattern = "rainbow"
    
    try:
        print("\nCommands:")
        print("  text:<message> - Set scrolling text")
        print("  color:<r>,<g>,<b> - Set text color")
        print("  brightness:<0-255> - Set brightness")
        print("  pattern:<name> - Show pattern (rainbow, spiral, wave)")
        print("  textmode - Switch to text mode")
        print("  clear - Clear display")
        print("  quit - Exit")
        print("")
        
        # Main loop
        last_update = time.time()
        frame_rate = 1/15  # 15 FPS
        
        while True:
            current_time = time.time()
            
            # Handle user input (non-blocking)
            import select
            import sys
            
            if select.select([sys.stdin], [], [], 0):
                user_input = input().strip()
                
                if user_input.lower() == 'quit':
                    break
                elif user_input.lower() == 'clear':
                    controller.clear_display()
                elif user_input.lower() == 'textmode':
                    pattern_mode = False
                    print("Switched to text mode")
                elif user_input.lower().startswith('text:'):
                    new_text = user_input[5:]
                    scroller.set_text(new_text)
                    pattern_mode = False
                    print(f"Text set to: {new_text}")
                elif user_input.lower().startswith('color:'):
                    try:
                        rgb = user_input[6:].split(',')
                        r, g, b = map(int, rgb)
                        scroller.color = (r, g, b)
                        print(f"Color set to RGB({r},{g},{b})")
                    except ValueError:
                        print("Invalid color format. Use r,g,b")
                elif user_input.lower().startswith('brightness:'):
                    try:
                        brightness = int(user_input[11:])
                        controller.set_brightness(brightness)
                        print(f"Brightness set to {brightness}")
                    except ValueError:
                        print("Invalid brightness value")
                elif user_input.lower().startswith('pattern:'):
                    pattern_name = user_input[8:].lower()
                    if pattern_name in ['rainbow', 'spiral', 'wave']:
                        current_pattern = pattern_name
                        pattern_mode = True
                        print(f"Pattern set to {pattern_name}")
                    else:
                        print("Unknown pattern. Available: rainbow, spiral, wave")
            
            # Update display at target frame rate
            if current_time - last_update >= frame_rate:
                if pattern_mode:
                    # Generate pattern
                    if current_pattern == "rainbow":
                        PatternGenerator.rainbow(matrix, pattern_offset)
                    elif current_pattern == "spiral":
                        PatternGenerator.spiral(matrix, pattern_offset)
                    elif current_pattern == "wave":
                        PatternGenerator.wave(matrix, pattern_offset)
                    pattern_offset += 0.1
                else:
                    # Update scrolling text
                    scroller.update()
                
                # Send frame to ESP32
                controller.send_frame(matrix)
                last_update = current_time
            
            time.sleep(0.01)  # Small delay to prevent high CPU usage
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        controller.disconnect()
        print("Goodbye!")


if __name__ == "__main__":
    main()