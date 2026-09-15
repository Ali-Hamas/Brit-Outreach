@echo off
echo ===================================================
echo   Starting Brit Outreach System (Backend & Frontend)
echo ===================================================

start "Brit Outreach Backend API (Port 8000)" cmd /k "cd /d m:\Brit Outreach System\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 3 /nobreak >nul

start "Brit Outreach Frontend Dashboard (Port 3000)" cmd /k "cd /d m:\Brit Outreach System\frontend && npm run dev"

echo.
echo ===================================================
echo   System Started Successfully!
echo   Dashboard: http://localhost:3000
echo   API Docs:  http://localhost:8000/docs
echo ===================================================
