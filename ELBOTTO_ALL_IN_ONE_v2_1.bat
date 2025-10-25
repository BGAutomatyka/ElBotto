
@echo off
chcp 65001 >nul
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
title ElBotto ALL-IN-ONE v2.1 (menu + logging)

set "RESULTS=results"
set "DATA=data"
if not exist "%RESULTS%" mkdir "%RESULTS%"
set "LOG=%RESULTS%\_allinone.log"
echo [BOOT] %DATE% %TIME% Working dir: %CD% > "%LOG%"

REM --- helper: log to console + file ---
:LOG
REM usage: call :LOG "message"
echo %~1
>>"%LOG%" echo %~1
exit /b 0

REM --- locate venv or create ---
set "PY=.venv\Scripts\python.exe"
set "PIP=.venv\Scripts\pip.exe"
if not exist "%PY%" (
  call :LOG "[INFO] .venv not found. Trying to create..."
  for %%P in (py python) do (
     where %%P >nul 2>&1 && (
        %%P -3.11 -m venv .venv || %%P -3 -m venv .venv || %%P -m venv .venv
     )
  )
  if not exist "%PY%" (
    call :LOG "[ERROR] Failed to create .venv. Install Python 3.11+ or create venv manually."
    goto MENU
  )
)

REM --- install essentials ---
if exist "%PIP%" (
  call :LOG "[INFO] Upgrading pip/setuptools/wheel..."
  "%PIP%" install --upgrade pip setuptools wheel >>"%LOG%" 2>&1
  call :LOG "[INFO] Installing extras: matplotlib pandas numpy feedparser transformers websockets pytest"
  "%PIP%" install matplotlib pandas numpy feedparser transformers websockets pytest >>"%LOG%" 2>&1
) else (
  call :LOG "[WARN] pip not found in .venv"
)

REM --- editable install if pyproject ---
if exist "pyproject.toml" (
  call :LOG "[INFO] Installing project (editable)"
  "%PIP%" install -e ".[dev]" >>"%LOG%" 2>&1
)

REM --- patch GUI (incl. Metrics tab) if app.py exists ---
if exist "elbotto_gui\app.py" (
  call :LOG "[PATCH] GUI tabs (WFV/Heatmap/Adapter+/Rules/Self-Test/Metrics)"
  call :PATCH_GUI
) else (
  call :LOG "[PATCH] elbotto_gui\app.py not found. Skipping GUI patch."
)

:MENU
echo.
echo ================== MENU (v2.1) ==================
echo 1^) Smoke test (toy -> features -> regime -> WFV -> heatmap)
echo 2^) Start LIVE (recorder + replay + paper + Adapter+ + GUI)
echo 3^) Run WFV on results\lob_features.csv
echo 4^) STOP LIVE
echo 5^) Open LOG
echo 6^) Exit
set /p CH=Choose [1-6]: 
if "%CH%"=="1" call :SMOKE_TEST & goto MENU
if "%CH%"=="2" call :START_LIVE & goto MENU
if "%CH%"=="3" call :RUN_WFV & goto MENU
if "%CH%"=="4" call :STOP_LIVE & goto MENU
if "%CH%"=="5" start "" notepad.exe "%LOG%" & goto MENU
if "%CH%"=="6" goto END
goto MENU

:SMOKE_TEST
call :LOG "[SMOKE] Starting..."
if exist "smoke_test\run_smoke_test.bat" (
  call smoke_test\run_smoke_test.bat >>"%LOG%" 2>&1
) else (
  if not exist "%DATA%" mkdir "%DATA%"
  if not exist "%RESULTS%" mkdir "%RESULTS%"
  "%PY%" smoke_test\make_toy_lob.py >>"%LOG%" 2>&1
  "%PY%" -m elbotto_ob.ob.featurizer --in data\toy_lob.csv --out results\lob_features.csv --levels 3 --agg-sec 1 >>"%LOG%" 2>&1
  "%PY%" -m elbotto_ob.regime.online --in results\lob_features.csv --out results\regime_state.json >>"%LOG%" 2>&1
  "%PY%" -m elbotto_patch.wfv.walk_forward --csv results\lob_features.csv --mode microprice --thresholds 0.05,0.10 --train-rows 20000 --test-rows 5000 --step-rows 5000 --out-prefix results\wfv >>"%LOG%" 2>&1
  "%PY%" -m elbotto_patch.viz.ob_heatmap --csv results\lob_features.csv --levels 3 --out results\ob_heatmap.png >>"%LOG%" 2>&1
)
call :LOG "[SMOKE] Done. Check 'results\'."
exit /b 0

:RUN_WFV
if not exist "%RESULTS%\lob_features.csv" (
  call :LOG "[WFV] results\lob_features.csv not found. Run smoke or featurizer first."
  exit /b 0
)
set "THR=0.05,0.10,0.15,0.20"
call :LOG "[WFV] Running..."
"%PY%" -m elbotto_patch.wfv.walk_forward --csv results\lob_features.csv --mode microprice --thresholds %THR% --train-rows 200000 --test-rows 50000 --step-rows 50000 --fee-bps 2 --latency-ms 50 --out-prefix results\wfv >>"%LOG%" 2>&1
call :LOG "[WFV] Done. See results\wfv_*.csv"
exit /b 0

:START_LIVE
call :LOG "[LIVE] Starting recorder + replay + paper + Adapter+ + GUI"
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
call :LOG "[LIVE] PIDs saved to results\live_pids.json"
exit /b 0

:STOP_LIVE
call :LOG "[STOP] Stopping live stack ..."
powershell -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='SilentlyContinue';" ^
  "if (Test-Path '%RESULTS%\live_pids.json') { $pids = Get-Content '%RESULTS%\live_pids.json' | ConvertFrom-Json; foreach($p in $pids){ try { Stop-Process -Id $p.pid -Force -ErrorAction SilentlyContinue } catch {} } Remove-Item '%RESULTS%\live_pids.json' -ErrorAction SilentlyContinue; Write-Host 'killed.' } else { Write-Host 'no pids file.' }"
exit /b 0

:PATCH_GUI
powershell -ExecutionPolicy Bypass -Command ^
  "$app = Join-Path (Get-Location) 'elbotto_gui\app.py'; if(!(Test-Path $app)){exit 0};" ^
  "$content = Get-Content $app -Raw;" ^
  "$imports = @('from elbotto_gui.tabs.wfv_tab import WFVTab','from elbotto_gui.tabs.heatmap_tab import HeatmapTab','from elbotto_gui.tabs.adapter_tab import AdapterPlusTab','from elbotto_gui.tabs.rules_editor_tab import RulesEditorTab','from elbotto_gui.tabs.selftest_tab import SelfTestTab','from elbotto_gui.tabs.metrics_tab import MetricsTab');" ^
  "foreach($i in $imports){ if($content -notmatch [regex]::Escape($i)){ $content = $i + \"`r`n\" + $content } }" ^
  "$adds = @('self.nb.add(WFVTab(self.nb), text=\"WFV\")','self.nb.add(HeatmapTab(self.nb), text=\"Heatmap\")','self.nb.add(AdapterPlusTab(self.nb), text=\"Adapter+\")','self.nb.add(RulesEditorTab(self.nb), text=\"Rules\")','self.nb.add(SelfTestTab(self.nb), text=\"Self-Test\")','self.nb.add(MetricsTab(self.nb), text=\"Metrics\")');" ^
  "if ($content -match 'self\.nb\s*=\s*ttk\.Notebook'){ foreach($a in $adds){ if($content -notmatch [regex]::Escape($a)){ $content += \"`r`n        $a\" } } } else { $content += \"`r`n# NOTE: Tabs appended; manual placement may be required.`r`n\" + ($adds -join \"`r`n        \") }" ^
  "Set-Content -Path $app -Value $content -Encoding UTF8; Write-Host 'GUI patched'"
exit /b 0

:END
echo.
echo Press any key to close...
pause >nul
endlocal
