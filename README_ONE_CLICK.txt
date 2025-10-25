
ElBotto – One-Click Runner
==========================
1) Skopiuj wszystkie wcześniejsze paczki (ULTRA+ AI, OrderBook PRO, WFV/Heatmap Patch, Integration Pack) do katalogu projektu i rozpakuj.
2) Skopiuj ten plik ZIP do katalogu projektu i rozpakuj.
3) Dwuklik: DOUBLE_CLICK_ME.bat

Co zrobi skrypt:
- sprawdzi/utworzy .venv (jeśli trzeba),
- zainstaluje extras (matplotlib/pandas/feedparser/transformers),
- załata GUI (doda zakładki: Self-Test, WFV, Heatmap, Adapter+, Rules),
- odpali smoke test (toy LOB → featury → regime → WFV → heatmapa),
- uruchomi Adapter+ i GUI.

Po starcie GUI przejdź do zakładki Self-Test (log), WFV (wyniki), Heatmap (PNG), Adapter+ (runtime_overrides.json).
