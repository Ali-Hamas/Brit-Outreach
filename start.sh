#!/bin/bash
# Start the Outreach System

echo "Starting Ascentra Global Outreach System..."

# Start backend
cd /var/www/outreach/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "Backend started on port 8000 (PID: $BACKEND_PID)"

# Start frontend
cd /var/www/outreach/frontend
npx vite preview --port 3000 --host 0.0.0.0 &
FRONTEND_PID=$!
echo "Frontend started on port 3000 (PID: $FRONTEND_PID)"

echo ""
echo "=== System Started ==="
echo "Frontend: http://your-ip:3000"
echo "Backend API: http://your-ip:8000"
echo "API Docs: http://your-ip:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
