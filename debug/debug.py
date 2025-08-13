#!/usr/bin/env python3
"""
Debug test script for WS2812B LED panels
Tests basic serial communication with ESP32
"""

import serial
import serial.tools.list_ports
import time
import sys


def find_esp32_port():
    """Auto-detect ESP32 port"""
    ports = serial.tools.list_ports.comports()
    esp32_ports = []
    
    print("Available serial ports:")
    for i, port in enumerate(ports):
        print(f"  {i}: {port.device} - {port.description}")
        # Check for common ESP32 identifiers
        if any(x in port.description.upper() for x in ['CH340', 'CP210', 'USB', 'ESP32', 'SERIAL']):
            esp32_ports.append(port.device)
    
    if esp32_ports:
        print(f"\nLikely ESP32 port(s): {esp32_ports}")
        return esp32_ports[0]
    return None


def test_basic_communication(port, baudrate=115200):
    """Test basic serial communication"""
    print(f"\nConnecting to {port} at {baudrate} baud...")
    
    try:
        # Open serial connection
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            timeout=2.0,
            write_timeout=2.0
        )
        
        # Clear any old data
        ser.reset_input_buffer()
        ser.reset_output_buffer()
        
        # Wait for ESP32 to initialize
        print("Waiting for ESP32 to initialize...")
        time.sleep(2)
        
        # Read any startup messages
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"ESP32: {line}")
        
        return ser
        
    except Exception as e:
        print(f"Failed to connect: {e}")
        return None


def run_tests(ser):
    """Run a series of LED tests"""
    
    tests = [
        ("Clear", "C"),
        ("Red", "R"),
        ("Green", "G"),
        ("Blue", "B"),
        ("Clear", "C"),
        ("Rainbow", "T"),
    ]
    
    print("\n" + "="*50)
    print("RUNNING LED TESTS")
    print("="*50)
    
    for test_name, command in tests:
        print(f"\nTest: {test_name}")
        print(f"Sending command: {command}")
        
        # Send command
        ser.write(command.encode())
        ser.flush()
        
        # Wait a moment
        time.sleep(0.5)
        
        # Read response
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"ESP32: {line}")
        
        # Wait before next test
        if command != "C":  # Don't wait after clear
            time.sleep(2)
    
    # Test custom colors
    print("\n" + "="*50)
    print("TESTING CUSTOM COLORS")
    print("="*50)
    
    custom_colors = [
        ("Purple", "P128,0,128"),
        ("Orange", "P255,128,0"),
        ("Cyan", "P0,255,255"),
    ]
    
    for color_name, command in custom_colors:
        print(f"\nSetting color: {color_name}")
        ser.write(command.encode())
        ser.write(b'\n')
        ser.flush()
        
        time.sleep(0.5)
        
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"ESP32: {line}")
        
        time.sleep(2)
    
    # Test panel order
    print("\n" + "="*50)
    print("TESTING PANEL ORDER (Snake Test)")
    print("="*50)
    print("Each panel will light up in sequence...")
    
    ser.write(b'S')
    ser.flush()
    
    # Let it run for a bit
    for i in range(10):
        time.sleep(0.5)
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"ESP32: {line}")
    
    # Clear at the end
    ser.write(b'C')
    ser.flush()


def test_individual_leds(ser, num_leds=10):
    """Test individual LED control"""
    print("\n" + "="*50)
    print("TESTING INDIVIDUAL LED CONTROL")
    print("="*50)
    
    # Clear first
    ser.write(b'C')
    ser.flush()
    time.sleep(0.5)
    
    # Light up first few LEDs in different colors
    colors = [
        (255, 0, 0),    # Red
        (0, 255, 0),    # Green
        (0, 0, 255),    # Blue
        (255, 255, 0),  # Yellow
        (255, 0, 255),  # Magenta
        (0, 255, 255),  # Cyan
        (255, 128, 0),  # Orange
        (128, 0, 255),  # Purple
        (255, 255, 255),# White
        (128, 128, 128),# Gray
    ]
    
    for i in range(min(num_leds, len(colors))):
        r, g, b = colors[i]
        command = f"I{i},{r},{g},{b}\n"
        print(f"LED {i}: RGB({r},{g},{b})")
        ser.write(command.encode())
        ser.flush()
        time.sleep(0.2)
        
        while ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"  ESP32: {line}")


def interactive_mode(ser):
    """Interactive command mode"""
    print("\n" + "="*50)
    print("INTERACTIVE MODE")
    print("="*50)
    print("Commands:")
    print("  R - Red test")
    print("  G - Green test")
    print("  B - Blue test")
    print("  W - White test (low brightness)")
    print("  C - Clear")
    print("  T - Rainbow test pattern")
    print("  S - Snake test (panel order)")
    print("  P<r,g,b> - Set all pixels to RGB")
    print("  I<index>,<r>,<g>,<b> - Set specific LED")
    print("  H<brightness> - Set brightness (0-255)")
    print("  Q - Quit")
    print("="*50)
    
    while True:
        command = input("\nEnter command: ").strip()
        
        if command.upper() == 'Q':
            break
            
        if command:
            # Send command
            if command[0].upper() in ['P', 'I', 'H']:
                ser.write(command.encode())
                ser.write(b'\n')
            else:
                ser.write(command[0].encode())
            ser.flush()
            
            # Read response
            time.sleep(0.5)
            while ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                print(f"ESP32: {line}")


def main():
    print("WS2812B LED Panel Debug Tool")
    print("="*50)
    
    # Find or select port
    port = find_esp32_port()
    
    if not port:
        port = input("\nEnter serial port manually (e.g., COM3 or /dev/ttyUSB0): ").strip()
    else:
        use_detected = input(f"\nUse detected port {port}? (y/n): ").lower()
        if use_detected != 'y':
            port = input("Enter serial port manually: ").strip()
    
    # Connect
    ser = test_basic_communication(port)
    
    if not ser:
        print("Failed to establish communication")
        return
    
    try:
        # Choose mode
        print("\n" + "="*50)
        print("SELECT MODE")
        print("="*50)
        print("1. Run automatic tests")
        print("2. Test individual LEDs")
        print("3. Interactive mode")
        print("4. All tests")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == '1':
            run_tests(ser)
        elif choice == '2':
            test_individual_leds(ser)
        elif choice == '3':
            interactive_mode(ser)
        elif choice == '4':
            run_tests(ser)
            test_individual_leds(ser)
            interactive_mode(ser)
        else:
            print("Invalid choice")
            
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        # Clear and close
        print("\nCleaning up...")
        ser.write(b'C')
        ser.flush()
        time.sleep(0.5)
        ser.close()
        print("Connection closed")


if __name__ == "__main__":
    main()