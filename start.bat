@echo off
echo =======================================================
echo          STARTING OYBIT DEV ENVIRONMENT
echo =======================================================

echo.
echo [1/2] Starting Backend (FastAPI) on Port 8000...
start "Oybit Backend" cmd /k "uvicorn backend.main:app --reload --port 8000"

echo [2/2] Starting Frontend on Port 3000...
start "Oybit Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo =======================================================
echo Both servers are booting up in separate windows!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo =======================================================
