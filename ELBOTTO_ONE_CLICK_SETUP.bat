@echo off
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ELBOTTO_FULL_SETUP.ps1"
pause
