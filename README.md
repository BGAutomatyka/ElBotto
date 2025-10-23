# ElBotto – prototyp bota mikrostrukturalnego na prawdziwych danych

Projekt przedstawia minimalny, ale w pełni działający pipeline analizy order booków Binance.
Cały kod jest napisany z myślą o bezpieczeństwie i oparciu na rzeczywistych próbkach danych
(plik `data/binance_order_book_small.csv`). Próbka została przygotowana z notowań z 4 marca
2024 r. dla par BTCUSDT oraz ETHUSDT i służy jako mały zestaw startowy.

## Struktura pakietu

```
src/elbotto/
├── __init__.py             # publiczne API
├── backtest/engine.py      # trening i ewaluacja na różnych interwałach event-time
├── bots/portfolio.py       # uruchamianie wielu botów na tych samych danych
├── core/config.py          # konfiguracja strategii i limity ryzyka
├── crossasset/dependencies.py # korelacje i lead-lag pomiędzy parami
├── data/orderbook.py       # wczytywanie prawdziwych obserwacji order book
├── exec/execution_policy.py    # decyzje pasywne/agresywne z budżetem poślizgu
├── exec/strategies/microstructure.py # strategia mikrostrukturalna z piramidowaniem zysków
├── gui/app.py              # prosty panel HTML z metrykami
├── microstructure/features.py   # inżynieria cech i analiza wielu interwałów
├── ml/models.py oraz objectives.py   # koszto-świadome uczenie regresji logistycznej
├── monitoring/metrics.py   # kontrole bezpieczeństwa
└── simulation/bootstrap.py # symulacje bazujące na bootstrapie z prawdziwych danych
```

## Szybki start

1. Zainstaluj zależności (Python 3.11+):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```

2. Uruchom backtest na dostarczonych danych:

   ```python
   from elbotto import Backtester, StrategyConfig, load_order_book_csv
   datasets = load_order_book_csv("data/binance_order_book_small.csv")
   reports = Backtester(StrategyConfig()).run(datasets)
   for symbol, report in reports.items():
       print(symbol, report.state.metrics)
   ```

3. Sprawdź zależności między parami i wygeneruj scenariusz bootstrap:

   ```python
   from elbotto import analyse_dependencies, bootstrap_scenarios
   deps = analyse_dependencies(datasets)
   scenario = bootstrap_scenarios(next(iter(datasets.values())), steps=8, seed=42)
   ```

4. Wygeneruj HTML panelu:

   ```python
   from elbotto import DashboardApp, StrategyConfig
   config = StrategyConfig()
   app = DashboardApp(config, reports)
   html = app.render()
   ```

5. Uruchom szybki start z linii poleceń i zobacz podsumowanie wskaźników:

   ```bash
   python -m elbotto data/binance_order_book_small.csv
   ```

   Polecenie wypisze liczbę transakcji, końcowy kapitał oraz najważniejsze cechy, które zwiększały i zmniejszały PnL.

## Jak pobrać większy zestaw danych z Binance

1. **Archiwalne zrzuty** – odwiedź [https://data.binance.vision](https://data.binance.vision) i pobierz ZIP-y z katalogów `spot/monthly/klines`, `spot/monthly/trades` albo `futures/um/daily/bookDepth`.
   Każdy plik ma obok siebie sumę kontrolną `.CHECKSUM`; po pobraniu zweryfikuj integralność:

   ```bash
   wget "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-03.zip"
   wget "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-03.zip.CHECKSUM"
   sha256sum -c BTCUSDT-1m-2024-03.zip.CHECKSUM
   ```

   Od 1 stycznia 2025 r. dane spot mają znaczniki czasu w mikrosekundach – parser `load_order_book_csv` obsługuje oba formaty.

2. **Synchronizacja order book w czasie rzeczywistym** – połącz snapshot REST (`/api/v3/depth` dla spot lub `/fapi/v1/depth` dla futures) z różnicowymi strumieniami WebSocket (`@depth`).
   Postępuj dokładnie według instrukcji Binance: pobierz snapshot, odfiltruj wiadomości o `u <= lastUpdateId`, a następnie stosuj strumień, pilnując zgodności numerów sekwencyjnych `pu`/`u` – w razie luki wykonaj pełną resynchronizację.

3. **Magazyn danych** – przekonwertuj pliki do Parquet i trzymaj w DuckDB (kolumny te same co w `data/binance_order_book_small.csv`). Pozwala to szybko analizować wiele par i interwałów bez ładowania wszystkiego do pamięci.

## Analiza wskaźników odpowiedzialnych za zysk i stratę

Moduł `elbotto.analysis.diagnostics.evaluate_feature_impacts` buduje macierz cech dla każdej pary, łączy ją z faktycznymi transakcjami strategii i liczy wpływ kwartylowy (dolny vs górny). W praktyce daje to listę „czerwonych flag” (cechy pogarszające wynik) i „zielonych flag” (cechy wzmacniające strategię). Przykład:

```python
from elbotto import Backtester, StrategyConfig, evaluate_feature_impacts, load_order_book_csv

datasets = load_order_book_csv("data/binance_order_book_small.csv")
reports = Backtester(StrategyConfig()).run(datasets)
impacts = evaluate_feature_impacts(datasets, reports)

print("Cechy strat:")
for effect in impacts.loss_drivers():
    print(effect)

print("Cechy zysku:")
for effect in impacts.gain_drivers():
    print(effect)
```

Najczęściej strata pojawia się, gdy wysoki jest VPIN (toksyczność) lub gdy przewidywana przewaga nie pokrywa opłat i poślizgu (duże `spread` i `queue_pressure`). Zysk generują kombinacje `microprice_edge` + dodatniego `imbalance` przy niskiej zmienności oraz szybkie ruchy wolumenu (`delta_volume`).

## Pakowanie projektu w jeden plik ZIP

Skrypt `scripts/package_release.py` przygotowuje archiwum, które można zainstalować przez `pip install`. Uruchom:

```bash
python scripts/package_release.py
```

W katalogu `dist/` pojawi się `elbotto_install_bundle.zip`. Możesz je zainstalować w czystym środowisku poleceniem `pip install elbotto_install_bundle.zip`. Skrypt używa tylko modułów standardowej biblioteki i dokleja `pyproject.toml`, katalog `src/` oraz przykładowe dane.

## Testy

```
pytest
```

Testy obejmują backtester, analizę zależności, panel HTML oraz symulacje bootstrapowe.

## Uwagi bezpieczeństwa

- Domyślnie pracujemy na historii (tryb "shadow"). Przed wejściem na rynek konieczne
  jest rozszerzenie modułów `live/` i przygotowanie bezpiecznego brokera.
- W kodzie zastosowano podstawowe limity ryzyka (`RiskLimits`), które powinny zostać
  skalibrowane przed produkcyjnym użyciem.
- Symulacje korzystają wyłącznie z próbek historycznych, nie generujemy sztucznych danych.

## Własne dane

Aby zwiększyć próbkę, należy przygotować plik CSV z kolumnami identycznymi jak w
`data/binance_order_book_small.csv`. Dane można pobrać np. z interfejsu
`/fapi/v1/depth` Binance lub z archiwów tickowych. W repozytorium pozostawiono jedynie
kilkanaście obserwacji jako przykład; docelowy model wymaga większych historii.
