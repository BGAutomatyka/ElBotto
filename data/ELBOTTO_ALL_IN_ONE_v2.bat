
@echo off
chcp 65001 >nul
setlocal ENABLEDELAYEDEXPANSION
title ElBotto ALL-IN-ONE v2 (menu+logging)

set LOG=results\_allinone.log
if not exist results mkdir results
echo [BOOT] %DATE% %TIME% Working dir: %CD% > "%LOG%"
set PY=.venv\Scripts\python.exe
set PIP=.venv\Scripts\pip.exe
set RESULTS=results
set DATA=data

if /I "%1"=="stop"  ( call :STOP_LIVE & goto :END )
if /I "%1"=="live"  ( call :START_LIVE & goto :MENU )
if /I "%1"=="smoke" ( call :SMOKE_TEST & goto :MENU )

if not exist "%PY%" (
  echo [INFO] .venv not found. Trying to create... | tee -a "%LOG%"
  for %%P in (py python) do (
     where %%P >nul 2>&1 && ( %%P -3 -m venv .venv && goto :venv_ok )
  )
  echo [ERROR] No system Python found. Install Python 3.11+ or create .venv manually. | tee -a "%LOG%"
  goto :HALT
)
:venv_ok

if exist "%PIP%" (
  echo [INFO] Upgrading pip/setuptools/wheel... | tee -a "%LOG%"
  "%PIP%" install --upgrade pip setuptools wheel >> "%LOG%" 2>&1
  echo [INFO] Installing extras ... | tee -a "%LOG%"
  "%PIP%" install matplotlib pandas numpy feedparser transformers websockets pytest >> "%LOG%" 2>&1
) else (
  echo [WARN] pip not found in .venv | tee -a "%LOG%"
)

if exist "pyproject.toml" (
  echo [INFO] Installing project (editable) ... | tee -a "%LOG%"
  "%PIP%" install -e ".[dev]" >> "%LOG%" 2>&1
)

if exist "elbotto_gui\app.py" (
  echo [PATCH] GUI tabs (WFV/Heatmap/Adapter+/Rules/Self-Test/Metrics) ... | tee -a "%LOG%"
  call :PATCH_GUI
) else (
  echo [PATCH] elbotto_gui\app.py not found. Skipping GUI patch. | tee -a "%LOG%"
)

goto :MENU

:MENU
echo.
echo ============== MENU (v2) ==============
echo 1^) Smoke test (toy -> features -> regime -> WFV -> heatmap)
echo 2^) Start LIVE stack (recorder + replay + paper + Adapter+ + GUI)
echo 3^) Run WFV on results\lob_features.csv
echo 4^) STOP LIVE stack
echo 5^) Open LOG (results\_allinone.log)
echo 6^) Exit
set /p CH=Choose [1-6]: 
if "%CH%"=="1" call :SMOKE_TEST & goto :MENU
if "%CH%"=="2" call :START_LIVE & goto :MENU
if "%CH%"=="3" call :RUN_WFV & goto :MENU
if "%CH%"=="4" call :STOP_LIVE & goto :MENU
if "%CH%"=="5" start "" notepad.exe "%LOG%" & goto :MENU
if "%CH%"=="6" goto :END
goto :MENU

:SMOKE_TEST
echo [SMOKE] Starting... | tee -a "%LOG%"
if exist "smoke_test\run_smoke_test.bat" (
  call smoke_test\run_smoke_test.bat >> "%LOG%" 2>&1
) else (
  if not exist "%DATA%" mkdir "%DATA%"
  if not exist "%RESULTS%" mkdir "%RESULTS%"
  "%PY%" smoke_test\make_toy_lob.py >> "%LOG%" 2>&1
  "%PY%" -m elbotto_ob.ob.featurizer --in data\toy_lob.csv --out results\lob_features.csv --levels 3 --agg-sec 1 >> "%LOG%" 2>&1
  "%PY%" -m elbotto_ob.regime.online --in results\lob_features.csv --out results\regime_state.json >> "%LOG%" 2>&1
  "%PY%" -m elbotto_patch.wfv.walk_forward --csv results\lob_features.csv --mode microprice --thresholds 0.05,0.10 --train-rows 20000 --test-rows 5000 --step-rows 5000 --out-prefix results\wfv >> "%LOG%" 2>&1
  "%PY%" -m elbotto_patch.viz.ob_heatmap --csv results\lob_features.csv --levels 3 --out results\ob_heatmap.png >> "%LOG%" 2>&1
)
echo [SMOKE] Done. Check 'results\' | tee -a "%LOG%"
exit /b 0

:RUN_WFV
if not exist "%RESULTS%\lob_features.csv" (
  echo [WFV] results\lob_features.csv not found. Run smoke or featurizer first. | tee -a "%LOG%"
  exit /b 0
)
set THR=0.05,0.10,0.15,0.20
echo [WFV] Running... | tee -a "%LOG%"
"%PY%" -m elbotto_patch.wfv.walk_forward --csv results\lob_features.csv --mode microprice --thresholds %THR% --train-rows 200000 --test-rows 50000 --step-rows 50000 --fee-bps 2 --latency-ms 50 --out-prefix results\wfv >> "%LOG%" 2>&1
echo [WFV] Done. See results\wfv_*.csv | tee -a "%LOG%"
exit /b 0

:START_LIVE
echo [LIVE] Starting recorder + replay + paper + Adapter+ + GUI ... | tee -a "%LOG%"
if not exist "%RESULTS%" mkdir "%RESULTS%"
if not exist "%DATA%\live" mkdir "%DATA%\live"
powershell -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='SilentlyContinue';" ^
  "$procs=@();" ^
  "function Start-Tracked([string]$File,[string]$Args,[string]$Name){$p=Start-Process -FilePath $File -ArgumentList $Args -PassThru; $procs+=@([pscustomobject]@{name=$Name; pid=$p.Id; file=$File; args=$Args})}" ^
  "Start-Tracked '%PY%' 'stream\live_binance_depth_recorder.py --symbol BTCUSDT --levels 10' 'recorder';" ^
  "Start-Tracked '%PY%' 'stream\replay_to_features.py --indir data\live --out results\lob_features_live.csv --levels 10' 'replay';" ^
  "Start-Tracked '%PY%' 'stream\paper_executor.py --features results\lob_features_live.csv --out results\equity_paper.csv' 'paper';" ^
  "if (Test-Path 'elbotto_patch\adapter\elbotto_runtime_adapter_plus.py') { Start-Tracked '%PY%' '-m elbotto_patch.adapter.elbotto_runtime_adapter_plus --results results --interval 5 --rules rules.json' 'adapter+' }" ^
  "if (Test-Path 'run_gui.bat') { Start-Tracked 'cmd.exe' '/c start \"\" run_gui.bat' 'gui' }" ^
  "$procs | ConvertTo-Json | Out-File -Encoding utf8 '%RESULTS%\live_pids.json';"
echo [LIVE] PIDs saved to results\live_pids.json | tee -a "%LOG%"
exit /b 0

:STOP_LIVE
echo [STOP] Stopping live stack ... | tee -a "%LOG%"
powershell -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='SilentlyContinue';" ^
  "if (Test-Path '%RESULTS%\live_pids.json') { $pids = Get-Content '%RESULTS%\live_pids.json' | ConvertFrom-Json; foreach($p in $pids){ try { Stop-Process -Id $p.pid -Force -ErrorAction SilentlyContinue } catch {} } Remove-Item '%RESULTS%\live_pids.json' -ErrorAction SilentlyContinue; Write-Host 'killed.' } else { Write-Host 'no pids file.' }"
exit /b 0

:PATCH_GUI
powershell -ExecutionPolicy Bypass -Command ^
  "$app = Join-Path (Get-Location) 'elbotto_gui\app.py';" ^
  "$content = Get-Content $app -Raw;" ^
  "$imports = @('from elbotto_gui.tabs.wfv_tab import WFVTab','from elbotto_gui.tabs.heatmap_tab import HeatmapTab','from elbotto_gui.tabs.adapter_tab import AdapterPlusTab','from elbotto_gui.tabs.rules_editor_tab import RulesEditorTab','from elbotto_gui.tabs.selftest_tab import SelfTestTab','from elbotto_gui.tabs.metrics_tab import MetricsTab');" ^
  "foreach($i in $imports){ if($content -notmatch [regex]::Escape($i)){ $content = $i + \"`r`n\" + $content } }" ^
  "$adds = @('self.nb.add(WFVTab(self.nb), text=\"WFV\")','self.nb.add(HeatmapTab(self.nb), text=\"Heatmap\")','self.nb.add(AdapterPlusTab(self.nb), text=\"Adapter+\")','self.nb.add(RulesEditorTab(self.nb), text=\"Rules\")','self.nb.add(SelfTestTab(self.nb), text=\"Self-Test\")','self.nb.add(MetricsTab(self.nb), text=\"Metrics\")');" ^
  "if ($content -match 'self\.nb\s*=\s*ttk\.Notebook'){ foreach($a in $adds){ if($content -notmatch [regex]::Escape($a)){ $content += \"`r`n        $a\" } } } else { $content += \"`r`n# NOTE: Tabs appended; manual placement may be required.`r`n\" + ($adds -join \"`r`n        \") }" ^
  "Set-Content -Path $app -Value $content -Encoding UTF8; Write-Host 'GUI patched'"
exit /b 0

:HALT
echo.
echo Press any key to close...
pause >nul
goto :END

:END
echo.
echo Bye.
pause
endlocal
