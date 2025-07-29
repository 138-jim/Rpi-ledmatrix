#!/usr/bin/env python3
"""
Raspberry Pi LED Matrix Controller
Controls ESP32 LED matrix via serial communication
"""

import serial
import time
import sys
import threading
from typing import Optional


class ESP32LEDController:
    def __init__(self, port: str = '/dev/ttyUSB0', baudrate: int = 115200):
        """
        Initialize the ESP32 LED controller
        
        Args:
            port: Serial port (usually /dev/ttyUSB0 or /dev/ttyACM0)
            baudrate: Communication speed (default 115200)
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_connection: Optional[serial.Serial] = None
        self.connected = False
    
    def set_brightness(self, brightness: int) -> bool:
        """
        Set LED brightness (0-255)
        Note: This requires custom ESP32 code to handle brightness commands
        """
        if 0 <= brightness <= 255:
            return self.send_message(f"BRIGHTNESS:{brightness}")
        return False
    
    def show_pattern(self, pattern: str) -> bool:
        """
        Display predefined patterns
        Available patterns: rainbow, snake, spiral, checkerboard, flash
        """
        patterns = ['rainbow', 'snake', 'spiral', 'checkerboard', 'flash']
        if pattern.lower() in patterns:
            return self.send_message(f"PATTERN:{pattern.upper()}")
        else:
            print(f"Unknown pattern. Available: {', '.join(patterns)}")
            return False
    
    def clear_display(self) -> bool:
        """Clear the LED matrix display"""
        return self.send_message("CLEAR")
    
    def set_color(self, r: int, g: int, b: int) -> bool:
        """
        Set text color (RGB values 0-255)
        Note: This requires custom ESP32 code to handle color commands
        """
        if all(0 <= val <= 255 for val in [r, g, b]):
            return self.send_message(f"COLOR:{r},{g},{b}")
        return False
    
    def set_scroll_speed(self, speed: int) -> bool:
        """
        Set scroll speed in milliseconds
        Note: This requires custom ESP32 code to handle speed commands
        """
        if speed > 0:
            return self.send_message(f"SPEED:{speed}")
        return False
        
    def connect(self) -> bool:
        """
        Establish serial connection to ESP32
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2
            )
            self.connected = True
            print(f"Connected to ESP32 on {self.port}")
            time.sleep(2)  # Allow ESP32 to reset
            return True
        except serial.SerialException as e:
            print(f"Failed to connect to {self.port}: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Close serial connection"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.connected = False
            print("Disconnected from ESP32")
    
    def send_message(self, message: str) -> bool:
        """
        Send text message to ESP32 for display
        
        Args:
            message: Text to display on LED matrix
            
        Returns:
            bool: True if sent successfully
        """
        if not self.connected or not self.serial_connection:
            print("Not connected to ESP32")
            return False
        
        try:
            # ESP32 reads until newline character
            self.serial_connection.write(f"{message}\n".encode())
            self.serial_connection.flush()
            print(f"Sent message: {message}")
            return True
        except serial.SerialException as e:
            print(f"Error sending message: {e}")
            return False
    
    def read_response(self, timeout: float = 1.0) -> Optional[str]:
        """
        Read response from ESP32
        
        Args:
            timeout: Read timeout in seconds
            
        Returns:
            Response string or None if timeout/error
        """
        if not self.connected or not self.serial_connection:
            return None
        
        try:
            self.serial_connection.timeout = timeout
            response = self.serial_connection.readline().decode().strip()
            return response if response else None
        except serial.SerialException as e:
            print(f"Error reading response: {e}")
            return None
    
    def get_available_ports(self) -> list:
        """
        Get list of available serial ports
        
        Returns:
            List of available port names
        """
        import serial.tools.list_ports
        ports = [port.device for port in serial.tools.list_ports.comports()]
        return ports


def main():
    """Main interactive loop"""
    print("ESP32 LED Matrix Controller")
    print("=" * 30)
    
    # Initialize controller
    controller = ESP32LEDController()
    
    # Show available ports
    ports = controller.get_available_ports()
    print(f"Available ports: {ports}")
    
    # Try to connect
    if not controller.connect():
        print("Failed to connect. Please check:")
        print("1. ESP32 is connected via USB")
        print("2. Correct port (try /dev/ttyACM0)")
        print("3. User has permission to access serial port")
        print("   Run: sudo usermod -a -G dialout $USER")
        print("   Then logout and login again")
        sys.exit(1)
    
    try:
        print("\nCommands:")
        print("  Type message to display")
        print("  'pattern:<name>' - show pattern (rainbow, snake, spiral, checkerboard, flash)")
        print("  'brightness:<0-255>' - set brightness")
        print("  'color:<r>,<g>,<b>' - set text color")
        print("  'speed:<ms>' - set scroll speed")
        print("  'clear' - clear display")
        print("  'quit' or 'exit' to stop")
        print("  'status' to check connection")
        print("")
        
        while True:
            user_input = input("Enter command: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                break
            elif user_input.lower() == 'status':
                print(f"Connected: {controller.connected}")
                if controller.connected:
                    print(f"Port: {controller.port}")
            elif user_input.lower() == 'clear':
                controller.clear_display()
            elif user_input.lower().startswith('pattern:'):
                pattern = user_input.split(':', 1)[1]
                controller.show_pattern(pattern)
            elif user_input.lower().startswith('brightness:'):
                try:
                    brightness = int(user_input.split(':', 1)[1])
                    controller.set_brightness(brightness)
                except ValueError:
                    print("Invalid brightness value. Use 0-255")
            elif user_input.lower().startswith('color:'):
                try:
                    rgb = user_input.split(':', 1)[1].split(',')
                    r, g, b = map(int, rgb)
                    controller.set_color(r, g, b)
                except ValueError:
                    print("Invalid color format. Use r,g,b (0-255)")
            elif user_input.lower().startswith('speed:'):
                try:
                    speed = int(user_input.split(':', 1)[1])
                    controller.set_scroll_speed(speed)
                except ValueError:
                    print("Invalid speed value. Use positive integer (milliseconds)")
            elif user_input:
                controller.send_message(user_input)
                
                # Read any response from ESP32
                response = controller.read_response(0.5)
                if response:
                    print(f"ESP32: {response}")
    
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    
    finally:
        controller.disconnect()
        print("Goodbye!")


if __name__ == "__main__":
    main()