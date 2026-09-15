#!/bin/bash
# Check status of all services

echo "=== Ascentra Global Outreach System Status ==="
echo ""

# Check backend
if pgrep -f "uvicorn app.main:app" > /dev/null; then
    echo "Backend: RUNNING (port 8000)"
else
    echo "Backend: STOPPED"
fi

# Check frontend
if pgrep -f "npm run preview" > /dev/null; then
    echo "Frontend: RUNNING (port 3000)"
else
    echo "Frontend: STOPPED"
fi

# Check Hermes
if systemctl is-active --quiet hermes; then
    echo "Hermes: RUNNING"
else
    echo "Hermes: STOPPED"
fi

# Check database
if [ -f "/var/www/outreach/backend/brit_outreach.db" ]; then
    SIZE=$(du -h /var/www/outreach/backend/brit_outreach.db | cut -f1)
    echo "Database: EXISTS ($SIZE)"
else
    echo "Database: NOT FOUND"
fi

echo ""
echo "=== Quick Actions ==="
echo "Start all:  ./start.sh"
echo "Stop all:   ./stop.sh"
echo "View logs:  journalctl -u outreach -f"
