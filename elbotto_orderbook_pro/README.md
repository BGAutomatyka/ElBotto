# ElBotto – Order Book PRO Pack

## Co w środku
- **OB Featurizer** (`ob/featurizer.py`): wyciąga cechy mikrostruktury z L2/L3 (mid, spread, microprice, OFI, queue imbalance, depth ratios, book slope, price pressure, cancellation rate, itp.).
- **OB Simulator** (`ob/sim_engine.py`): event‑driven backtest na diffach order booka; proste modelowanie latency i kolejki.
- **Regime Online** (`regime/online.py`): rolling RV/spread/OFI variance → `calm | trending | high_vol | illiquid` + eksport do `results/regime_state.json`.
- **Transformer Sentiment** (`news/transformer_sentiment.py`): próba użycia modelu HF (finBERT/pl) z cache; fallback do prostego słownikowego.
- **Contextual Bandit** (`ml/rl_bandit.py`): LinUCB/TS do strojenia progu/akcji na podstawie cech z OB.
- **Risk Kill‑Switch** (`risk/kill_switch.py`): nadzór DD/vol; zapisuje `pause_until` do `runtime_overrides.json`.
- **GUI tabs (stubs)**: `gui_tabs/tab_orderbook.py`, `gui_tabs/tab_regime_online.py` – możesz wpiąć do obecnego GUI.

## Minimalne runy
- Featurizer:
  ```bash
  .venv\Scripts\python.exe run_ob_featurizer.py --in data\lob.csv --out results\lob_features.csv --levels 10 --agg-sec 1
  ```
- Regime online:
  ```bash
  .venv\Scripts\python.exe regime\online.py --in results\lob_features.csv --out results\regime_state.json
  ```
- Bandit:
  ```bash
  .venv\Scripts\python.exe ml\rl_bandit.py --csv results\lob_features.csv --reward-col pnl --context-cols ofi microprice_imb q_imb spread
  ```

## Integracja
- GUI (ULTRA/AI): dodaj Tab z `gui_tabs`, lub odpal runy zewnętrzne i czytaj `results/*.json` w adapterze.
- Bot live: w pętli wczytuj `runtime_overrides.json` + `regime_state.json` i koryguj sygnały/risk.
