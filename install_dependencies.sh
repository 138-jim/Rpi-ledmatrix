#!/bin/bash

echo "Installing dependencies for LED Matrix Controller..."

# Update system
sudo apt update

# Install Python3 and pip
sudo apt install -y python3 python3-pip

# Install system dependencies for Pillow
sudo apt install -y python3-dev libjpeg-dev zlib1g-dev

# Install Python packages
pip3 install -r requirements.txt

# Add user to dialout group for serial access
sudo usermod -a -G dialout $USER

# Make scripts executable
chmod +x led_matrix_controller.py

echo ""
echo "Installation complete!"
echo ""
echo "IMPORTANT: Logout and login again for group changes to take effect."
echo ""
echo "Usage:"
echo "  python3 led_matrix_controller.py"
echo ""
echo "Upload esp32_frame_display.ino to your ESP32 first!"