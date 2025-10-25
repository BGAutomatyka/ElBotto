@echo off
chcp 65001 >nul
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] .venv\Scripts\python.exe not found. Create venv first.
  pause & exit /b 1
)
"%PY%" gui_standalone.py
