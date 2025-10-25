@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d "%~dp0"

echo.
echo ===============================
echo   ElBotto - setup and run
echo ===============================
echo.

where python >NUL 2>&1
if errorlevel 1 (
  echo [ERROR] Python not found in PATH. Install Python 3.11+ and check "Add to PATH".
  pause
  exit /b 1
)

if not exist ".venv" (
  echo [INFO] Creating virtual environment .venv ...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create .venv
    pause
    exit /b 1
  )
) else (
  echo [INFO] Detected existing .venv
)

set "PY=.venv\Scripts\python.exe"
if not exist "%PY%" (
  echo [ERROR] %PY% not found.
  pause
  exit /b 1
)

echo [INFO] Upgrading pip/setuptools/wheel ...
"%PY%" -m pip install --upgrade pip setuptools wheel

if exist "pyproject.toml" (
  echo [INFO] Installing from pyproject.toml ...
  "%PY%" -m pip install -e .[dev] || "%PY%" -m pip install -e .
) else if exist "requirements.txt" (
  echo [INFO] Installing from requirements.txt ...
  "%PY%" -m pip install -r requirements.txt
) else (
  echo [WARN] No pyproject.toml or requirements.txt found. Skipping deps install.
)

echo.
echo [INFO] Starting ElBotto ...
if exist "src\elbotto\__main__.py" (
  "%PY%" "src\elbotto\__main__.py"
) else (
  "%PY%" -m elbotto
)

echo.
echo [DONE] Finished.
pause
