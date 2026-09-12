#!/bin/bash

###############################################################################
# AWS EC2 DEPLOYMENT SCRIPT FOR 8-BOT TRADING SYSTEM
# Region: ap-south-1 (Asia Pacific - Mumbai)
# Instance Type: t2.micro (Free tier)
# OS: Ubuntu 22.04 LTS
# Running Time: Market hours only (09:00-15:30 IST)
###############################################################################

set -e

echo "=========================================="
echo "8-BOT SYSTEM AWS DEPLOYMENT"
echo "=========================================="
echo ""

# Update system
echo "[1/10] Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python 3.14
echo "[2/10] Installing Python 3.14..."
sudo apt-get install -y python3.14 python3.14-venv python3-pip
python3.14 --version

# Install Git
echo "[3/10] Installing Git..."
sudo apt-get install -y git
git --version

# Install required system packages
echo "[4/10] Installing system dependencies..."
sudo apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    wget \
    nano \
    htop

# Clone repository
echo "[5/10] Cloning GitHub repository..."
cd /home/ubuntu
git clone https://github.com/vivekjhamumbai-byte/quant-trading-bots-unified.git
cd quant-trading-bots-unified

# Create virtual environment
echo "[6/10] Creating Python virtual environment..."
python3.14 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "[7/10] Installing Python packages..."
pip install --upgrade pip
pip install flask flask-cors python-dotenv requests

# Create necessary directories
echo "[8/10] Creating directories..."
mkdir -p logs/dashboard
mkdir -p kill_switch
mkdir -p data
mkdir -p backups

# Set up environment file
echo "[9/10] Setting up environment configuration..."
cat > .env << 'EOF'
MSTOCK_USER_ID=
MSTOCK_PASSWORD=
MSTOCK_API_KEY=
MSTOCK_TOTP_CODE=
AWS_REGION=ap-south-1
INSTANCE_ID=$(ec2-metadata --instance-id | cut -d " " -f 2)
DEPLOYMENT_DATE=$(date +%Y-%m-%d)
EOF

echo "⚠️  MANUAL STEP REQUIRED:"
echo "Edit .env file and add your mStock credentials:"
echo "sudo nano .env"
echo ""

# Create systemd service for auto-start
echo "[10/10] Setting up systemd service for auto-start..."
sudo tee /etc/systemd/system/trading-bots.service > /dev/null << 'EOF'
[Unit]
Description=8-Bot Trading System
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/quant-trading-bots-unified
Environment="PATH=/home/ubuntu/quant-trading-bots-unified/venv/bin"
ExecStart=/home/ubuntu/quant-trading-bots-unified/venv/bin/python run_bot.py --all
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/trading-bots.log
StandardError=append:/var/log/trading-bots-error.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable trading-bots.service

# Create market hours scheduler
echo "Creating market hours scheduler..."
cat > /home/ubuntu/market_hours_scheduler.py << 'EOF'
#!/usr/bin/env python3
"""
Market Hours Scheduler for AWS EC2
Starts bots at 09:00 IST, stops at 15:30 IST
"""

import subprocess
import schedule
import time
from datetime import datetime
import pytz

IST = pytz.timezone('Asia/Kolkata')

def start_bots():
    print(f"[{datetime.now(IST)}] Starting bots...")
    subprocess.run(['sudo', 'systemctl', 'start', 'trading-bots.service'])
    print("Bots started!")

def stop_bots():
    print(f"[{datetime.now(IST)}] Stopping bots...")
    subprocess.run(['sudo', 'systemctl', 'stop', 'trading-bots.service'])
    print("Bots stopped!")

if __name__ == "__main__":
    # Schedule bots to start at 09:00 IST
    schedule.every().day.at("09:00").do(start_bots)

    # Schedule bots to stop at 15:30 IST
    schedule.every().day.at("15:30").do(stop_bots)

    print("Market hours scheduler running...")
    print("Start time: 09:00 IST")
    print("Stop time: 15:30 IST")

    while True:
        schedule.run_pending()
        time.sleep(60)
EOF

chmod +x /home/ubuntu/market_hours_scheduler.py

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "Next Steps:"
echo "1. Edit .env file with your credentials:"
echo "   nano /home/ubuntu/quant-trading-bots-unified/.env"
echo ""
echo "2. Start the trading bots:"
echo "   sudo systemctl start trading-bots.service"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status trading-bots.service"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u trading-bots.service -f"
echo ""
echo "5. Access dashboard:"
echo "   http://YOUR-EC2-PUBLIC-IP:8765"
echo ""
echo "=========================================="
