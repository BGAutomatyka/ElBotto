@echo off
set PY=.venv\Scripts\python.exe
set PIP=.venv\Scripts\pip.exe
if not exist "%PY%" (
  echo [ERROR] .venv not found.
  pause
  exit /b 1
)
"%PIP%" install --upgrade pip setuptools wheel
"%PIP%" install matplotlib pandas numpy feedparser transformers
echo [DONE] Installed extras.
pause
