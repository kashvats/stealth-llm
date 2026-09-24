@echo off
title Project Runner
cd /d "%~dp0"
echo ========================================================
echo               PROJECT RUNNER
echo ========================================================
echo.
echo Please select how you want to run the project:
echo 1. Run Locally
echo.
set /p choice="Enter your choice: "

if "%choice%"=="1" (
    echo.
    echo Starting Local Environment...
    echo.
    python main.py
    pause
    exit
)

echo Invalid choice. Exiting.
pause