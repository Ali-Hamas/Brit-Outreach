#!/bin/bash
# One-click installation script for VPS

set -e

echo "=== Ascentra Global Outreach System Installer ==="
echo ""

# Step 1: Update system
echo "[1/6] Updating system..."
apt update && apt upgrade -y

# Step 2: Install dependencies
echo "[2/6] Installing dependencies..."
apt install -y python3 python3-pip python3-venv nodejs npm git curl

# Step 3: Setup backend
echo "[3/6] Setting up backend..."
cd /var/www/outreach/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Step 4: Setup database
echo "[4/6] Setting up database..."
cd /var/www/outreach
cd /var/www/outreach
python AscentraOutreach/setup.py

# Step 5: Setup frontend
echo "[5/6] Setting up frontend..."
cd /var/www/outreach/frontend
npm install
npm run build

# Step 6: Setup permissions
echo "[6/6] Setting up permissions..."
chmod +x /var/www/outreach/start.sh
chmod +x /var/www/outreach/stop.sh
chmod +x /var/www/outreach/status.sh

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Start the system:"
echo "  ./start.sh"
echo ""
echo "Access the system:"
echo "  Frontend: http://your-ip:3000"
echo "  Backend:  http://your-ip:8000"
echo ""
echo "To install Hermes AI agent:"
echo "  curl -LsSf https://nousresearch.com/hermes/install.sh | sh"
echo ""
