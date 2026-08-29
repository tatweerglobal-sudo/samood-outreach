@echo off
title Samood Email Outreach Server
chcp 65001 > nul
cls

echo ====================================================================
echo      Samood Email Outreach Engine - Server Starting...
echo ====================================================================
echo.

:: فتح المتصفح تلقائياً بعد ثانيتين
start "" "http://127.0.0.1:8000"

:: تشغيل السيرفر
python -m uvicorn main:app --host 127.0.0.1 --port 8000
