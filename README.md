# ElBotto – kompletny program do handlu mikrostrukturalnego

Projekt rozwinął się z prototypu w kompletny pakiet, który można uruchomić zarówno jako
bibliotekę, jak i gotowy program (`elbotto`). Kod koncentruje się na bezpiecznym handlu
mikrostrukturalnym na podstawie prawdziwych obserwacji order booków Binance (plik
`data/binance_order_book_small.csv` zawiera próbkę z 4 marca 2024 r. dla par BTCUSDT oraz
ETHUSDT).

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
├── exec/strategies/microstructure.py # strategia mikrostrukturalna z piramidowaniem zysków i podziałem zysku na spot/reinwestycję
├── gui/app.py              # panel HTML z ręcznym sterowaniem, auto-tuningiem i kontrolą kapitału
├── microstructure/features.py   # inżynieria cech i analiza wielu interwałów
├── ml/models.py oraz objectives.py   # koszto-świadome uczenie regresji logistycznej
├── monitoring/metrics.py   # kontrole bezpieczeństwa
└── simulation/bootstrap.py # symulacje bazujące na bootstrapie z prawdziwych danych
```

## Szybki start (program i biblioteka)

1. Zainstaluj zależności (Python 3.11+):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```

2. Uruchom jako program – domyślnie uruchamia się podkomenda `backtest`:

   ```bash
   python -m elbotto
   # lub równoważnie
   elbotto backtest data/binance_order_book_small.csv --show-deps
   ```

   Dostępne są również inne komendy:

   | Komenda | Opis |
   | --- | --- |
   | `elbotto analyse` | tworzy raport z transakcji, rekomendacje i analizę kontrfaktyczną |
   | `elbotto autotune` | uruchamia auto-kalibrację parametrów i (opcjonalnie) zapisuje wynik do JSON |
   | `elbotto gui --auto` | generuje panel HTML z przyciskiem „Automat” i pełną telemetrią |
   | `elbotto simulate` | buduje scenariusz bootstrapowy oraz wskazuje najsilniejszą zależność między parami |
   | `elbotto package` | pakuje projekt w pojedynczy plik ZIP gotowy do instalacji |

   Każda komenda przyjmuje te same opcjonalne parametry konfiguracyjne, np.
   `--decision-threshold`, `--profit-spot-ratio` czy `--risk-max-vpin`. Dzięki temu
   konfigurację można zmieniać bezpośrednio z GUI lub wiersza poleceń.

   Jeśli wolisz nie korzystać z terminala, możesz także uruchomić aplikację
   podwójnym kliknięciem pliku [`run_elbotto.py`](run_elbotto.py) (na Windows)
   lub poleceniem `python run_elbotto.py` w innych systemach. Skrypt startuje
   domyślny backtest i otwiera wszystkie moduły aplikacji.

3. Przykład użycia jako biblioteka – pełny backtest i analiza wpływu cech:

   ```python
   from elbotto import Backtester, StrategyConfig, load_order_book_csv
   datasets = load_order_book_csv("data/binance_order_book_small.csv")
   reports = Backtester(StrategyConfig()).run(datasets)
   for symbol, report in reports.items():
       print(symbol, report.state.metrics)
   ```

4. Sprawdź zależności między parami i wygeneruj scenariusz bootstrap:

   ```python
   from elbotto import analyse_dependencies, bootstrap_scenarios
   deps = analyse_dependencies(datasets)
   scenario = bootstrap_scenarios(next(iter(datasets.values())), steps=8, seed=42)
   ```

5. Wygeneruj HTML panelu wraz z możliwością sterowania bez CLI lub skorzystaj z
   klasy `ElBottoApplication`, która spina cały program:

```python
from elbotto import DashboardApp, ElBottoApplication, StrategyConfig
config = StrategyConfig(profit_spot_ratio=0.55, strong_signal_multiplier=1.6)
app = DashboardApp.from_dataset(config, "data/binance_order_book_small.csv")
# ręczna zmiana parametrów (np. próg decyzyjny, udział zysku na spot i wolumen sondy)
app.manual_update(decision_threshold=0.6, profit_spot_ratio=0.6, probe_ratio=0.2)
# automatyczna kalibracja jednym wywołaniem
app.auto_optimize()
html = app.render()

pro = ElBottoApplication(config, dataset="data/binance_order_book_small.csv")
reports, impacts, deps = pro.run_backtest(include_dependencies=True)
dashboard_html = pro.render_dashboard(auto=True)
bundle = pro.package("elbotto_release.zip")
```

Wygenerowany panel zawiera:

- bieżący podział kapitału (kapitał handlowy vs. oszczędności spot),
- tabelę transakcji z informacją o reinwestycji, trybie wejścia (standard/strong/probe) i pewności sygnału,
- sekcję "Automat" z rezultatami siatki mini-backtestów (również dla parametrów `profit_spot_ratio`, `strong_signal_multiplier` i `probe_ratio`),
- rekomendacje kalibracji na podstawie rzeczywistych transakcji oraz porównanie decyzji z niewykorzystanymi okazjami.

6. Panel HTML oraz GUI generowane z poziomu `elbotto gui` zawierają te same informacje – dzięki temu nie ma potrzeby korzystać z CLI podczas codziennej pracy, choć wszystkie akcje (auto-tuning, zapis rekomendacji, pakowanie projektu) są także dostępne z wiersza poleceń.

### Interaktywny serwer GUI

Od wersji 0.4 możesz uruchomić pełny panel www z formularzami uruchamiającymi wszystkie
dotychczasowe komendy CLI:

```bash
elbotto gui data/binance_order_book_small.csv --serve --host 127.0.0.1 --port 8080
```

Na stronie znajdują się:

- edytowalne pola dla każdego parametru strategii (w tym limitów ryzyka i podziału zysku na spot/reinwestycję),
- przyciski `Backtest`, `Analiza decyzji`, `Automat`, `Symulacja` i `Pakiet`, które działają bezpośrednio jak komendy CLI,
- log zdarzeń prezentujący wyniki akcji, historię auto-tuningu oraz podgląd ostatniej symulacji,
- sekcja z aktualnym stanem kapitału, tabelą transakcji w USD i podsumowaniem rekomendacji.

Zmiany w konfiguracji zapisują się od razu, a przycisk „Automat” rozszerza siatkę parametrów
o dodatkowe warianty, korzystając z tego samego mechanizmu co polecenie `elbotto autotune`.

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

Moduł `analysis.trade_review` dodatkowo:

- raportuje, jaka część zysku trafiła na spot, a jaka została reinwestowana,
- liczy ile niewykorzystanych okazji (kontrfaktycznych) pojawiło się przy aktualnych progach,
- sugeruje korekty parametrów (`decision_threshold`, `profit_spot_ratio`, `probe_ratio`, `min_reserve_ratio` itd.) w oparciu o realne wyniki.

Wyniki są widoczne w panelu HTML w sekcji „Analiza przyczyn” oraz „Historia transakcji”.

## Pakowanie projektu w jeden plik ZIP

Archiwum instalacyjne możesz przygotować na dwa sposoby:

```bash
elbotto package --output elbotto_install_bundle.zip
# lub równoważnie
python scripts/package_release.py
```

W katalogu `dist/` pojawi się wskazane archiwum, które da się zainstalować w czystym środowisku poleceniem `pip install elbotto_install_bundle.zip`. Mechanizm korzysta wyłącznie ze standardowej biblioteki i dokleja `pyproject.toml`, katalog `src/` oraz przykładowe dane.

## Testy

```
pytest
```

Testy obejmują backtester, analizę zależności, panel HTML oraz symulacje bootstrapowe.

## Współpraca między asystentami

Jeżeli nad projektem równolegle pracuje kilka modeli (np. ChatGPT i Codex),
postępuj według zaleceń z pliku [COLLABORATION.md](COLLABORATION.md). Opisuje on
wspólną gałąź `collab/integration`, zasady synchronizacji oraz sposób dzielenia
się wynikami testów i raportami.

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
