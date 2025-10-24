# ElBotto – ULTRA+ AI Integration Pack

## Instalacja
1. Skopiuj foldery `elbotto_gui/`, `elbotto_patch/`, `tools/`, `smoke_test/` do katalogu projektu (obok `.venv`, `src`, `results`, `data`).  
2. Otwórz `PATCH_APP_INSTRUCTIONS.txt` i dopisz 4 importy + 4 zakładki w `elbotto_gui/app.py`.  
3. (Opcjonalnie) uruchom `tools/install_extras.bat` (matplotlib/pandas/feedparser/transformers).

## Test krok po kroku
- `tools/diag_env.py` – szybka diagnostyka środowiska.  
- `smoke_test/run_smoke_test.bat` – pełny „dymek”: toy LOB → featury → regime → WFV → heatmapa.  
- W GUI pojawią się zakładki: **WFV**, **Heatmap**, **Adapter+**, **Rules**.

## Uwaga
- Na własnych danych historycznych pamiętaj o mapowaniu kolumn L2/L3. Jeśli nazwy różnią się od `bid1/bid1_qty/...`, przerób featurizer lub zrób mapper.
