#!/bin/bash
# Stop the Outreach System

echo "Stopping Ascentra Global Outreach System..."

# Kill backend
pkill -f "uvicorn app.main:app"
echo "Backend stopped"

# Kill frontend
pkill -f "npm run preview"
echo "Frontend stopped"

# Kill Hermes
systemctl stop hermes 2>/dev/null
echo "Hermes stopped"

echo ""
echo "=== All Services Stopped ==="
