# ElBotto – Control Center (ULTRA+ AI)

Dodatki:
- **News AI**: RSS + lokalny CSV, prosta analiza sentymentu, wygładzanie EMA per symbol, „News weight”.
- **Automation / Manual**: master switch + per-element (Strategy/Risk/News). W AUTO parametry są korygowane tuż przed runem.
- **Adaptive policy**: heurystyka łącząca reżim, wolatylność (placeholder) i sentyment do korekt progu/risku/max position.
- **Integracja**: wpływ newsów trafia do `best_config.json` (jeśli rozszerzysz bota o odczyt), a GUI reguluje argumenty runa.

Konfiguracja News:
- RSS (domyślnie Google News „bitcoin”), include/exclude frazy, interwał odpytywania.
- Opcjonalnie CSV z kolumnami: `ts,source,headline,sentiment(optional),symbols(optional)`.

Uwaga: aby mieć zatrzymanie procesu i wszystkie zakładki z wersji ULTRA, rozpakuj **ULTRA** i **ULTRA+ AI** obok — taby się dograją automatycznie.
