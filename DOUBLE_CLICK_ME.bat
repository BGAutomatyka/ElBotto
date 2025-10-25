
@echo off
chcp 65001 >nul
setlocal ENABLEDELAYEDEXPANSION
title ElBotto One-Click Runner

echo.
echo === ElBotto One-Click Runner ===
echo Working dir: %CD%
echo.

REM 1) Ensure venv or try to create
set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
  echo [INFO] .venv not found. Attempting to create with system Python...
  for %%P in (py python) do (
     where %%P >nul 2>&1 && (
        %%P -3 -m venv .venv && goto :venv_ok
     )
  )
  echo [ERROR] Cannot find system Python to create .venv. Please install Python 3.11+ or create .venv manually.
  pause
  exit /b 1
)
:venv_ok
set PY=.venv\Scripts\python.exe
set PIP=.venv\Scripts\pip.exe

REM 2) Install extras if available
if exist "tools\install_extras.bat" (
  call tools\install_extras.bat
) else (
  echo [WARN] tools\install_extras.bat not found. Skipping extras install.
)

REM 3) Patch GUI (imports + tabs). ExecutionPolicy bypass.
if exist "PATCH_GUI.ps1" (
  powershell -ExecutionPolicy Bypass -File ".\PATCH_GUI.ps1"
) else (
  echo [WARN] PATCH_GUI.ps1 not found. Skipping GUI patch.
)

REM 4) Diagnostics
if exist "tools\diag_env.py" (
  "%PY%" tools\diag_env.py
) else (
  echo [WARN] tools\diag_env.py not found. Skipping diagnostics.
)

REM 5) Smoke test (toy LOB -> featury -> regime -> WFV -> heatmap)
if exist "smoke_test\run_smoke_test.bat" (
  call smoke_test\run_smoke_test.bat
) else (
  echo [WARN] smoke_test\run_smoke_test.bat not found. Skipping smoke test.
)

REM 6) Start Adapter+ (if available)
if exist "tools\run_adapter_plus.bat" (
  start "" tools\run_adapter_plus.bat
) else (
  REM fallback
  if exist ".venv\Scripts\python.exe" if exist "elbotto_patch\adapter\elbotto_runtime_adapter_plus.py" (
    start "" ".venv\Scripts\python.exe" -m elbotto_patch.adapter.elbotto_runtime_adapter_plus --results results --interval 5 --rules rules.json
  ) else (
    echo [WARN] Adapter+ not found. Skipping.
  )
)

REM 7) Launch GUI
if exist "run_gui.bat" (
  start "" run_gui.bat
  echo [OK] GUI started in a new window. Check tabs: Self-Test, WFV, Heatmap, Adapter+, Rules.
) else (
  echo [WARN] run_gui.bat not found.
)

echo.
echo === DONE ===
echo If something failed above, scroll up for the first [ERROR] or [WARN].
pause
exit /b 0
