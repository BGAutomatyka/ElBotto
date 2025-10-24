"""Prosty interfejs CLI do uruchomienia backtestu i analizy."""

from __future__ import annotations

import argparse
from pathlib import Path

from elbotto.runtime.quickstart import run_quickstart


def main() -> None:
    parser = argparse.ArgumentParser(description="Szybkie uruchomienie bota ElBotto")
    parser.add_argument(
        "dataset",
        nargs="?",
        default="data/binance_order_book_small.csv",
        help="Ścieżka do pliku CSV z danymi order book",
    )
    args = parser.parse_args()
    reports, impacts = run_quickstart(Path(args.dataset))
    for symbol, report in reports.items():
        metrics = report.state.metrics
        print(f"=== {symbol} ===")
        print(f"Transakcji: {metrics['trade_count']}, końcowy kapitał: {metrics['final_equity']:.2f}")
    print("\nNajważniejsze cechy zwiększające zysk:")
    for effect in impacts.gain_drivers():
        print(f" + {effect.feature}: ΔPnL={effect.difference:.4f}")
    print("\nCechy odpowiadające za straty:")
    for effect in impacts.loss_drivers():
        print(f" - {effect.feature}: ΔPnL={effect.difference:.4f}")


if __name__ == "__main__":
    main()
