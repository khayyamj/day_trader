#!/bin/bash
# Trading Bot Deployment Setup Script

set -e  # Exit on error

echo "========================================="
echo "Trading Bot Deployment Setup"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/trading-bot"
SERVICE_NAME="trading-bot"
SERVICE_FILE="trading-bot.service"
LOG_DIR="/var/log/trading-bot"
USER="trading"
GROUP="trading"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    exit 1
fi

echo -e "${GREEN}Step 1: Creating user and directories${NC}"

# Create user if it doesn't exist
if ! id "$USER" &>/dev/null; then
    useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$USER"
    echo -e "${GREEN}✓ Created user: $USER${NC}"
else
    echo -e "${YELLOW}User $USER already exists${NC}"
fi

# Create log directory
mkdir -p "$LOG_DIR"
chown "$USER:$GROUP" "$LOG_DIR"
chmod 755 "$LOG_DIR"
echo -e "${GREEN}✓ Created log directory: $LOG_DIR${NC}"

# Create application directory if it doesn't exist
if [ ! -d "$INSTALL_DIR" ]; then
    mkdir -p "$INSTALL_DIR"
    chown "$USER:$GROUP" "$INSTALL_DIR"
    echo -e "${GREEN}✓ Created install directory: $INSTALL_DIR${NC}"
else
    echo -e "${YELLOW}Install directory already exists: $INSTALL_DIR${NC}"
fi

echo -e "\n${GREEN}Step 2: Installing systemd service${NC}"

# Copy service file
if [ ! -f "$SERVICE_FILE" ]; then
    echo -e "${RED}Error: $SERVICE_FILE not found in current directory${NC}"
    exit 1
fi

cp "$SERVICE_FILE" "/etc/systemd/system/$SERVICE_NAME.service"
chmod 644 "/etc/systemd/system/$SERVICE_NAME.service"
echo -e "${GREEN}✓ Copied service file to /etc/systemd/system/${NC}"

# Reload systemd
systemctl daemon-reload
echo -e "${GREEN}✓ Reloaded systemd${NC}"

echo -e "\n${GREEN}Step 3: Enabling service${NC}"

# Enable service
systemctl enable "$SERVICE_NAME.service"
echo -e "${GREEN}✓ Enabled $SERVICE_NAME service${NC}"

echo -e "\n${GREEN}========================================="
echo "Deployment Setup Complete!"
echo "=========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Copy your application files to $INSTALL_DIR"
echo "2. Set up your .env file at $INSTALL_DIR/.env"
echo "3. Install Python dependencies in $INSTALL_DIR/backend/venv"
echo "4. Start the service:"
echo "   sudo systemctl start $SERVICE_NAME"
echo ""
echo "Useful commands:"
echo "  Start:   sudo systemctl start $SERVICE_NAME"
echo "  Stop:    sudo systemctl stop $SERVICE_NAME"
echo "  Restart: sudo systemctl restart $SERVICE_NAME"
echo "  Status:  sudo systemctl status $SERVICE_NAME"
echo "  Logs:    sudo journalctl -u $SERVICE_NAME -f"
echo "  App logs: tail -f $LOG_DIR/app.log"
echo "  Errors:  tail -f $LOG_DIR/error.log"
