from pathlib import Path
import csv, json
def export_trades_csv(trades, outpath: Path):
    outpath.parent.mkdir(exist_ok=True, parents=True)
    with outpath.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["time","symbol","side","qty","price","pnl"])
        w.writeheader()
        for t in trades: w.writerow({k: t.get(k) for k in ["time","symbol","side","qty","price","pnl"]})
def export_equity_csv(times, equity, outpath: Path):
    outpath.parent.mkdir(exist_ok=True, parents=True)
    with outpath.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["time","equity"])
        for t,e in zip(times,equity): w.writerow([t,e])
