@echo off
setlocal EnableDelayedExpansion
title Oybit Launcher

echo ==============================================
echo        Oybit Test Environment Launcher
echo ==============================================
echo.
echo Starting Frontend Command Center...
echo Note: Checking if npm install is needed.
start "Oybit Command Center (Frontend)" cmd /k "cd /d "%~dp0Frontend Dashbaord" & if not exist node_modules (npm install) & npm run dev"
echo Frontend launched in a new window!
echo.

:MENU
echo ==============================================
echo Which bot backend would you like to start?
echo ==============================================
echo 1. Facebook Page       (Port 8001)
echo 2. Facebook Personal   (Port 8002)
echo 3. Instagram Brand     (Port 8003)
echo 4. Instagram Personal  (Port 8004)
echo 5. LinkedIn            (Port 8005)
echo 6. Reddit              (Port 8006)
echo 7. Telegram            (Port 8007)
echo 8. Exit
echo.

set /p choice="Enter a number (1-8): "

if "%choice%"=="1" set bot_dir=facebook_page
if "%choice%"=="2" set bot_dir=facebook_personal
if "%choice%"=="3" set bot_dir=instagram_brand
if "%choice%"=="4" set bot_dir=instagram_personal
if "%choice%"=="5" set bot_dir=linkedin
if "%choice%"=="6" set bot_dir=reddit
if "%choice%"=="7" set bot_dir=telegram
if "%choice%"=="8" goto EOF

if not defined bot_dir (
    echo.
    echo Invalid choice, please try again.
    echo.
    goto MENU
)

echo.
echo Starting %bot_dir% backend in a new window...
start "%bot_dir% Backend" cmd /k "cd /d "%~dp0%bot_dir%" && python main.py"
echo.

set bot_dir=
goto MENU

:EOF
echo Exiting...
