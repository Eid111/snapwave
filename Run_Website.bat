@echo off
chcp 65001 >nul
title SnapWave - Video & Audio Downloader Web Engine
cd /d "%~dp0"

echo ======================================================================
echo                SnapWave - High-Performance Web Engine
echo ======================================================================
echo.
echo [i] Starting server at: http://localhost:8000
echo [i] Press Ctrl+C in this window to stop the server.
echo.

start "" "http://localhost:8000"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

if errorlevel 1 (
    echo.
    echo [!] Server exited with an error. Please check your Python environment.
    pause >nul
)
