@echo off
setlocal
set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
  echo [ERROR] .venv not found.
  pause
  exit /b 1
)
echo [1/5] Generating toy LOB...
"%PY%" smoke_test\make_toy_lob.py || goto :err

echo [2/5] Featurizing...
"%PY%" -m elbotto_ob.ob.featurizer --in data	oy_lob.csv --out results\lob_features.csv --levels 3 --agg-sec 1 || goto :err

echo [3/5] Regime...
"%PY%" -m elbotto_ob.regime.online --in results\lob_features.csv --out resultsegime_state.json || goto :err

echo [4/5] WFV...
"%PY%" -m elbotto_patch.wfv.walk_forward --csv results\lob_features.csv --mode microprice --thresholds 0.05,0.1,0.15 --train-rows 100000 --test-rows 25000 --step-rows 25000 || goto :err

echo [5/5] Heatmap...
"%PY%" -m elbotto_patch.viz.ob_heatmap --csv results\lob_features.csv --levels 3 --out results\ob_heatmap.png || goto :err

echo [OK] Smoke test finished. Check results folder.
pause
exit /b 0
:err
echo [ERROR] Smoke test failed.
pause
exit /b 1
