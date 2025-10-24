
@echo off
chcp 65001 >nul
setlocal ENABLEDELAYEDEXPANSION
title ElBotto ALL-IN-ONE

:: Usage:
::   ELBOTTO_ALL_IN_ONE.bat           -> menu (diagnostics, smoke, WFV, LIVE start)
::   ELBOTTO_ALL_IN_ONE.bat live      -> directly start LIVE stack
::   ELBOTTO_ALL_IN_ONE.bat stop      -> stop LIVE stack (kills started PIDs)
::   ELBOTTO_ALL_IN_ONE.bat smoke     -> run smoke test (toy LOB -> features -> regime -> WFV -> heatmap)

echo.
echo ==============================
echo   ElBotto - ALL IN ONE
echo ==============================
echo Working dir: %CD%
echo.

set PY=.venv\Scripts\python.exe
set PIP=.venv\Scripts\pip.exe
set RESULTS=results
set DATA=data

if /I "%1"=="stop" goto :STOP_LIVE
if /I "%1"=="live" goto :START_LIVE
if /I "%1"=="smoke" goto :SMOKE_TEST

:: Ensure venv
if not exist "%PY%" (
  echo [INFO] .venv not found. Attempting to create with system Python...
  for %%P in (py python) do (
     where %%P >nul 2>&1 && (
        %%P -3 -m venv .venv && goto :venv_ok
     )
  )
  echo [ERROR] Cannot find system Python to create .venv. Install Python 3.11+ or create .venv manually.
  pause
  exit /b 1
)
:venv_ok

:: Install extras (matplotlib, pandas, numpy, feedparser, transformers, websockets, pytest)
if exist "%PIP%" (
  echo [INFO] Upgrading pip/setuptools/wheel...
  "%PIP%" install --upgrade pip setuptools wheel >nul
  echo [INFO] Installing extras...
  "%PIP%" install matplotlib pandas numpy feedparser transformers websockets pytest >nul
) else (
  echo [WARN] pip not found in .venv
)

:: Editable install if pyproject exists
if exist "pyproject.toml" (
  echo [INFO] Installing project (editable)...
  "%PIP%" install -e ".[dev]" || echo [WARN] Editable install failed, continuing...
)

:: Auto-patch GUI (imports + tabs). Create temp PS1 and run with bypass.
set PATCHPS=%TEMP%\_elbotto_patch_gui.ps1
> "%PATCHPS%" (
  echo Set-StrictMode -Version Latest
  echo $ErrorActionPreference = "Stop"
  echo $app = Join-Path (Get-Location) "elbotto_gui\app.py"
  echo if (!(Test-Path $app)) { Write-Host "[PATCH] elbotto_gui\app.py not found. Skipping."; exit 0 }
  echo $content = Get-Content $app -Raw
  echo $imports = @(
  echo  ^"from elbotto_gui.tabs.wfv_tab import WFVTab^",
  echo  ^"from elbotto_gui.tabs.heatmap_tab import HeatmapTab^",
  echo  ^"from elbotto_gui.tabs.adapter_tab import AdapterPlusTab^",
  echo  ^"from elbotto_gui.tabs.rules_editor_tab import RulesEditorTab^",
  echo  ^"from elbotto_gui.tabs.selftest_tab import SelfTestTab^"
  echo )
  echo foreach ($imp in $imports) { if ($content -notmatch [regex]::Escape($imp)) { $content = $imp + "`r`n" + $content; Write-Host "[PATCH] Added import: $imp" } }
  echo $adds = @(
  echo  ^"self.nb.add(WFVTab(self.nb), text=^"WFV^")^",
  echo  ^"self.nb.add(HeatmapTab(self.nb), text=^"Heatmap^")^",
  echo  ^"self.nb.add(AdapterPlusTab(self.nb), text=^"Adapter+^")^",
  echo  ^"self.nb.add(RulesEditorTab(self.nb), text=^"Rules^")^",
  echo  ^"self.nb.add(SelfTestTab(self.nb), text=^"Self-Test^")^"
  echo )
  echo if ($content -match "self\.nb\s*=\s*ttk\.Notebook") {
  echo   foreach ($add in $adds) { if ($content -notmatch [regex]::Escape($add)) { $content += "`r`n        $add" ; Write-Host "[PATCH] Added tab: $add" } }
  echo } else {
  echo   $content += "`r`n# NOTE: Could not locate Notebook creation; tabs appended may require manual placement.`r`n"
  echo   foreach ($add in $adds) { if ($content -notmatch [regex]::Escape($add)) { $content += "`r`n        $add" ; Write-Host "[PATCH] Appended: $add" } }
  echo }
  echo Set-Content -Path $app -Value $content -Encoding UTF8
  echo Write-Host "[PATCH] Done."
)
powershell -ExecutionPolicy Bypass -File "%PATCHPS%"

:: Diagnostics
if exist "tools\diag_env.py" (
  "%PY%" tools\diag_env.py
) else (
  echo [WARN] tools\diag_env.py not found. Skipping diagnostics.
)

:: Optional: quick pytest if tests present
if exist "tests" (
  echo [INFO] Running quick unit tests (pytest -q)...
  "%PY%" -m pytest -q || echo [WARN] pytest returned non-zero (continuing)...
)

:MAIN_MENU
echo.
echo ============ MENU ============
echo 1^) Smoke test (toy -> features -> regime -> WFV -> heatmap)
echo 2^) Start LIVE stack (recorder + replay + paper + Adapter+ + GUI)
echo 3^) Run WFV on results\lob_features.csv
echo 4^) STOP LIVE stack
echo 5^) Exit
set /p CH=Choose [1-5]: 
if "%CH%"=="1" goto :SMOKE_TEST
if "%CH%"=="2" goto :START_LIVE
if "%CH%"=="3" goto :RUN_WFV
if "%CH%"=="4" goto :STOP_LIVE
if "%CH%"=="5" goto :EOF
goto :MAIN_MENU

:SMOKE_TEST
echo [SMOKE] Starting...
if exist "smoke_test\run_smoke_test.bat" (
  call smoke_test\run_smoke_test.bat
) else (
  echo [SMOKE] no batch found, running steps...
  if not exist "%DATA%" mkdir "%DATA%"
  if not exist "%RESULTS%" mkdir "%RESULTS%"
  "%PY%" smoke_test\make_toy_lob.py || goto :smoke_err
  "%PY%" -m elbotto_ob.ob.featurizer --in data\toy_lob.csv --out results\lob_features.csv --levels 3 --agg-sec 1 || goto :smoke_err
  "%PY%" -m elbotto_ob.regime.online --in results\lob_features.csv --out results\regime_state.json || goto :smoke_err
  "%PY%" -m elbotto_patch.wfv.walk_forward --csv results\lob_features.csv --mode microprice --thresholds 0.05,0.10 --train-rows 20000 --test-rows 5000 --step-rows 5000 --out-prefix results\wfv || goto :smoke_err
  "%PY%" -m elbotto_patch.viz.ob_heatmap --csv results\lob_features.csv --levels 3 --out results\ob_heatmap.png || goto :smoke_err
)
echo [SMOKE] Done. Check 'results\'.
goto :MAIN_MENU
:smoke_err
echo [ERROR] Smoke test failed.
goto :MAIN_MENU

:RUN_WFV
if not exist "%RESULTS%\lob_features.csv" (
  echo [WFV] results\lob_features.csv not found. Run featurizer first or smoke test.
  goto :MAIN_MENU
)
set THR=0.05,0.10,0.15,0.20
"%PY%" -m elbotto_patch.wfv.walk_forward --csv results\lob_features.csv --mode microprice --thresholds %THR% --train-rows 200000 --test-rows 50000 --step-rows 50000 --fee-bps 2 --latency-ms 50 --out-prefix results\wfv
echo [WFV] Done. See results\wfv_*.csv
goto :MAIN_MENU

:START_LIVE
echo [LIVE] Starting live stack...
if not exist "%RESULTS%" mkdir "%RESULTS%"
if not exist "%DATA%\live" mkdir "%DATA%\live"

:: Use PowerShell to start processes and record PIDs
powershell -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='SilentlyContinue';" ^
  "$procs=@();" ^
  "function Start-Tracked([string]$File,[string]$Args,[string]$Name){$p=Start-Process -FilePath $File -ArgumentList $Args -PassThru; $procs+=@([pscustomobject]@{name=$Name; pid=$p.Id; file=$File; args=$Args})}" ^
  "Start-Tracked '%PY%' 'stream\live_binance_depth_recorder.py --symbol BTCUSDT --levels 10' 'recorder';" ^
  "Start-Tracked '%PY%' 'stream\replay_to_features.py --indir data\live --out results\lob_features_live.csv --levels 10' 'replay';" ^
  "Start-Tracked '%PY%' 'stream\paper_executor.py --features results\lob_features_live.csv --out results\equity_paper.csv' 'paper';" ^
  "if (Test-Path 'elbotto_patch\adapter\elbotto_runtime_adapter_plus.py') { Start-Tracked '%PY%' '-m elbotto_patch.adapter.elbotto_runtime_adapter_plus --results results --interval 5 --rules rules.json' 'adapter+' }" ^
  "if (Test-Path 'run_gui.bat') { Start-Tracked 'cmd.exe' '/c start \"\" run_gui.bat' 'gui' }" ^
  "$procs | ConvertTo-Json | Out-File -Encoding utf8 '%RESULTS%\live_pids.json';" ^
  "Write-Host 'PIDs saved to %RESULTS%\live_pids.json'"
echo [LIVE] Started. To stop: ELBOTTO_ALL_IN_ONE.bat stop
goto :EOF

:STOP_LIVE
echo [STOP] Stopping live stack...
if not exist "%RESULTS%\live_pids.json" (
  echo [STOP] No PID file found: %RESULTS%\live_pids.json
  goto :EOF
)
powershell -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='SilentlyContinue';" ^
  "$pids = Get-Content '%RESULTS%\live_pids.json' | ConvertFrom-Json;" ^
  "foreach($p in $pids){ try { Stop-Process -Id $p.pid -Force -ErrorAction SilentlyContinue; Write-Host ('killed '+$p.name+' pid='+$p.pid) } catch {} }" ^
  "Remove-Item '%RESULTS%\live_pids.json' -ErrorAction SilentlyContinue"
echo [STOP] Done.
goto :EOF

:EOF
echo.
echo === EXIT ===
endlocal
