"""Szybki start do uruchomienia strategii na prawdziwych danych."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from elbotto.analysis.diagnostics import ImpactReport, evaluate_feature_impacts
from elbotto.backtest.engine import BacktestReport, Backtester
from elbotto.core.config import StrategyConfig
from elbotto.data.orderbook import OrderBookSeries, load_order_book_csv


DEFAULT_DATASET = Path("data/binance_order_book_small.csv")


def run_quickstart(
    dataset_path: Path | str = DEFAULT_DATASET,
    config: StrategyConfig | None = None,
    series_map: Dict[str, OrderBookSeries] | None = None,
) -> Tuple[Dict[str, BacktestReport], ImpactReport]:
    """Uruchamia backtest i analizę wpływu cech na zadanym zbiorze danych."""

    if series_map is None:
        path = Path(dataset_path)
        if not path.exists():
            raise FileNotFoundError(f"Nie znaleziono pliku z danymi: {path}")
        series_map = load_order_book_csv(path)
    effective_config = config or StrategyConfig(decision_threshold=0.55)
    backtester = Backtester(effective_config)
    reports = backtester.run(series_map)
    impacts = evaluate_feature_impacts(series_map, reports)
    return reports, impacts
