@echo off
chcp 65001 > nul
title SnapWave - Start Online Public Server
cd /d "%~dp0"

echo ========================================================
echo        SnapWave - Starting Public Online Server...
echo ========================================================
python -X utf8 run_online.py
pause
