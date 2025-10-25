@echo off
cd /d "%~dp0"
set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] .venv not found. Run setup_env.bat first.
  pause
  exit /b 1
)
"%PY%" gui_main.py
