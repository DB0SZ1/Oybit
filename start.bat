@echo off
echo =======================================================
echo          STARTING OYBIT DEV ENVIRONMENT
echo =======================================================

echo.
echo [1/2] Starting Backend (FastAPI) on Port 8000...
start "Oybit Backend" cmd /k "uvicorn backend.main:app --reload --port 8000"

echo [2/3] Starting Frontend on Port 3000...
start "Oybit Frontend" cmd /k "cd frontend && npm run dev"

echo [3/3] Starting MiroFish Sidecar on Port 5001...
start "Oybit MiroFish" cmd /k "cd mirofish && npm run dev"

echo.
echo =======================================================
echo All servers are booting up in separate windows!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo MiroFish: http://localhost:5001
echo =======================================================
