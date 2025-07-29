#!/bin/bash

echo "Setting up Raspberry Pi for ESP32 LED control..."

# Update system
echo "Updating system packages..."
sudo apt update

# Install Python3 and pip if not present
echo "Installing Python3 and pip..."
sudo apt install -y python3 python3-pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Add user to dialout group for serial access
echo "Adding user to dialout group..."
sudo usermod -a -G dialout $USER

# Make the Python script executable
chmod +x rpi_led_controller.py

echo ""
echo "Setup complete!"
echo ""
echo "IMPORTANT: You need to logout and login again for group changes to take effect."
echo ""
echo "Usage:"
echo "  python3 rpi_led_controller.py"
echo ""
echo "Common serial ports:"
echo "  /dev/ttyUSB0 (USB-to-serial adapter)"
echo "  /dev/ttyACM0 (USB CDC device)"
echo ""
echo "To find your ESP32 port, run: ls /dev/tty*"