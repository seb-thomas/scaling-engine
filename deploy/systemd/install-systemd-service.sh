#!/bin/bash
# Install systemd service for scaling-engine
# Run this script on the server as root

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_FILE="$SCRIPT_DIR/scaling-engine.service"
SYSTEMD_DIR="/etc/systemd/system"
TARGET_FILE="$SYSTEMD_DIR/scaling-engine.service"

if [ ! -f "$SERVICE_FILE" ]; then
    echo "Error: Service file not found at $SERVICE_FILE"
    exit 1
fi

# Copy service file
echo "Installing systemd service..."
cp "$SERVICE_FILE" "$TARGET_FILE"

# Reload systemd
systemctl daemon-reload

# Enable service to start on boot
systemctl enable scaling-engine.service

echo "Systemd service installed and enabled."
echo "To start the service now, run: systemctl start scaling-engine"
echo "To check status, run: systemctl status scaling-engine"

