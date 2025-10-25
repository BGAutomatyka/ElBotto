@echo off
set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
  echo [ERROR] .venv not found.
  pause
  exit /b 1
)

echo [1/6] Env diag
"%PY%" tools\diag_env.py || goto :err

echo [2/6] Toy LOB
"%PY%" smoke_test\make_toy_lob.py || goto :err

echo [3/6] Featurize
"%PY%" -m elbotto_ob.ob.featurizer --in data	oy_lob.csv --out results\lob_features.csv --levels 3 --agg-sec 1 || goto :err

echo [4/6] Regime
"%PY%" -m elbotto_ob.regime.online --in results\lob_features.csv --out resultsegime_state.json || goto :err

echo [5/6] WFV
"%PY%" -m elbotto_patch.wfv.walk_forward --csv results\lob_features.csv --mode microprice --thresholds 0.05,0.10 --train-rows 20000 --test-rows 5000 --step-rows 5000 --out-prefix results\wfv || goto :err

echo [6/6] Heatmap
"%PY%" -m elbotto_patch.viz.ob_heatmap --csv results\lob_features.csv --levels 3 --out results\ob_heatmap.png || goto :err

echo [OK] CLI test complete. Check 'results' folder.
pause
exit /b 0

:err
echo [ERROR] CLI test failed.
pause
exit /b 1
