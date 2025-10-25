# run_quickstart_tuned.py
# Użycie:
#   python run_quickstart_tuned.py --dataset data/binance_order_book_small.csv ^
#       --threshold 0.50 --capital 5000 --max-position 1.0 --fee 0.0002 --windows 3 6 9
#
# Wypisze metryki + ranking cech.
import argparse
from pathlib import Path
from elbotto.runtime.quickstart import run_quickstart
from elbotto.core.config import StrategyConfig

def main():
    p = argparse.ArgumentParser(description="ElBotto quickstart z dostrajaniem parametrów")
    p.add_argument("--dataset", default="data/binance_order_book_small.csv")
    p.add_argument("--threshold", type=float, default=0.55)
    p.add_argument("--capital", type=float, default=5000.0)
    p.add_argument("--max-position", type=float, default=0.75, dest="maxpos")
    p.add_argument("--fee", type=float, default=0.0004, help="prowizja (np. 0.0004 = 4 bps)")
    p.add_argument("--windows", nargs="+", type=int, default=[3,6,9])
    args = p.parse_args()

    cfg = StrategyConfig(
        decision_threshold=args.threshold,
        capital=args.capital,
        max_position=args.maxpos,
        fee_rate=args.fee,
        evaluation_windows=tuple(args.windows),
    )
    reports, impacts = run_quickstart(Path(args.dataset), cfg)

    for symbol, report in reports.items():
        m = report.state.metrics
        print(f"=== {symbol} ===")
        print(f"Transakcji: {m['trade_count']}, końcowy kapitał: {m['final_equity']:.2f}")
    print("\nNajważniejsze cechy zwiększające zysk:")
    for e in impacts.gain_drivers():
        print(f" + {e.feature}: ΔPnL={e.difference:.4f}")
    print("\nCechy odpowiadające za straty:")
    for e in impacts.loss_drivers():
        print(f" - {e.feature}: ΔPnL={e.difference:.4f}")

if __name__ == "__main__":
    main()
