#!/bin/bash
# Installation script for LED Matrix Bluetooth Bridge

set -e  # Exit on error

echo "========================================="
echo "LED Matrix Bluetooth Bridge Installer"
echo "========================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "Warning: This doesn't appear to be a Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project root: $PROJECT_ROOT"
echo ""

# Install system dependencies
echo "[1/5] Installing system dependencies..."
apt-get update
apt-get install -y \
    python3-pip \
    python3-dev \
    libdbus-1-dev \
    libglib2.0-dev \
    bluetooth \
    bluez \
    libbluetooth-dev

echo ""

# Install Python dependencies
echo "[2/5] Installing Python dependencies..."
# Use --break-system-packages for modern Raspberry Pi OS (Bookworm+)
# This is safe for system services with minimal dependencies
pip3 install --break-system-packages -r "$SCRIPT_DIR/requirements.txt"

echo ""

# Enable Bluetooth
echo "[3/5] Enabling Bluetooth..."
systemctl enable bluetooth
systemctl start bluetooth

# Make BLE server executable
chmod +x "$SCRIPT_DIR/ble_server.py"

echo ""

# Create systemd service
echo "[4/5] Installing systemd service..."
cat > /etc/systemd/system/bluetooth-bridge.service << EOF
[Unit]
Description=LED Matrix Bluetooth Bridge
After=network.target bluetooth.target led-driver.service
Wants=bluetooth.target
Requires=led-driver.service

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/ble_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Allow Bluetooth access
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
systemctl daemon-reload

echo ""

# Ask user if they want to enable and start the service
echo "[5/5] Service installation complete"
echo ""
read -p "Enable service to start on boot? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl enable bluetooth-bridge.service
    echo "Service enabled"
fi

echo ""
read -p "Start service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl start bluetooth-bridge.service
    echo "Service started"
    echo ""
    echo "Check status with: sudo systemctl status bluetooth-bridge.service"
    echo "View logs with: sudo journalctl -u bluetooth-bridge.service -f"
fi

echo ""
echo "========================================="
echo "Installation complete!"
echo "========================================="
echo ""
echo "The Bluetooth bridge will advertise as 'LED Matrix'"
echo ""
echo "Useful commands:"
echo "  Start:   sudo systemctl start bluetooth-bridge.service"
echo "  Stop:    sudo systemctl stop bluetooth-bridge.service"
echo "  Restart: sudo systemctl restart bluetooth-bridge.service"
echo "  Status:  sudo systemctl status bluetooth-bridge.service"
echo "  Logs:    sudo journalctl -u bluetooth-bridge.service -f"
echo ""
echo "You can now connect to the display from your iPhone app!"
echo ""
