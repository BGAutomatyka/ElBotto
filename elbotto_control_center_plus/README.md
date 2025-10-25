
# ElBotto – Control Center (PLUS)

Super-rozszerzone GUI do pełnej kontroli nad botem:
- **Indicators window** (oddzielne okno, wyszukiwarka, select all/none, zapis do JSON)
- **Data Sweep** (dużo plików / chunking ogromnych CSV)
- **Batch Sweep** (siatka po threshold)
- **Charts** (ΔPnL features via matplotlib, opcjonalnie)
- **Model Lab** (szybkie modele sklearn/xgboost na CSV)
- **Training / Backtest / Analysis / Paper-Live**
- **Live „Aktualne wartości”** + eksport metryk do CSV

## Użycie
1. Rozpakuj w katalogu projektu (obok `.venv/`, `src/`, `data/`)
2. Uruchom: `run_gui.bat` (używa `.venv\Scripts\python.exe`)
3. W GUI:
   - Wejdź w **Indicators…** i wybierz cechy do analizy (opcjonalnie append `--indicators`).
   - W **Analysis / Backtest** wybierz skrypty i parametry.
   - **Data Sweep**: wskaż folder i pattern, ustaw chunking (jeśli duże pliki).
   - **Charts**: po zakończeniu runa narysuj bar-plot ΔPnL (jeśli jest matplotlib).
   - **Model Lab**: podaj CSV (features+label), wybierz model i uruchom.

> Uwaga: jeśli Twoje skrypty nie rozpoznają `--indicators`, zostaw odznaczone „Append selected indicators to args”
> – a lista i tak zapisze się do `results/selected_indicators.json`.

## Wymagania
- Python 3.11+ w `.venv`
- pakiety: tkinter (wbudowany), pandas/sklearn (tylko dla Model Lab), matplotlib (opcjonalnie dla wykresów), xgboost (opcjonalnie)

