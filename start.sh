#!/bin/bash
# Start the Outreach System

echo "Starting Ascentra Global Outreach System..."

# Start backend
cd /var/www/outreach/backend
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8005 > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started on port 8005 (PID: $BACKEND_PID)"

# Start frontend
cd /var/www/outreach/frontend
nohup npx vite preview --port 3005 --host 0.0.0.0 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started on port 3005 (PID: $FRONTEND_PID)"

echo ""
echo "=== System Started ==="
echo "Frontend: http://your-ip:3005"
echo "Backend API: http://your-ip:8005"
echo "API Docs: http://your-ip:8005/docs"
echo ""
echo "Press Ctrl+C to stop all services"
