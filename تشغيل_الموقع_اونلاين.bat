@echo off
chcp 65001 > nul
title SnapWave - تشغيل الموقع اونلاين
cd /d "%~dp0"

echo ========================================================
echo        SnapWave - جاري تشغيل الموقع أونلاين مجاناً...
echo ========================================================
python -X utf8 run_online.py
pause
