import argparse, json, time, pandas as pd
from pathlib import Path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--equity", default="results/equity_latest.csv")
    ap.add_argument("--out", default="results/runtime_overrides.json")
    ap.add_argument("--max-dd", type=float, default=0.05, help="max drawdown fraction")
    ap.add_argument("--cooldown", type=int, default=300, help="pause seconds when DD exceeded")
    a = ap.parse_args()
    p = Path(a.equity)
    if not p.exists(): 
        print("[KS] equity not found"); return
    import numpy as np
    df = pd.read_csv(p)
    e = df["equity"].values
    peak = -1e9; dd=0.0
    for v in e:
        peak = max(peak, v)
        dd = max(dd, (peak - v)/max(1e-9, peak))
    if dd >= a.max_dd:
        out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
        o = {"pause_until": time.time()+a.cooldown, "kill_switch":"drawdown", "drawdown": float(dd)}
        out.write_text(json.dumps(o, indent=2), encoding="utf-8")
        print("[KS] PAUSE written", o)
    else:
        print("[KS] OK dd=", dd)

if __name__ == "__main__":
    main()
