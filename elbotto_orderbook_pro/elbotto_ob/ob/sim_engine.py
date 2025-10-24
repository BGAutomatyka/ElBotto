from __future__ import annotations
import argparse, csv, math, random, time
from pathlib import Path

def simulate(feat_csv, out_csv, latency_ms=50, fee_bps=2.0, signal_col='microprice_imb', thr=0.1):
    pnl = 0.0; pos = 0; entries=0; exits=0
    with open(feat_csv, 'r', encoding='utf-8') as f, open(out_csv, 'w', encoding='utf-8', newline='') as out:
        rd = csv.DictReader(f)
        w = csv.DictWriter(out, fieldnames=['ts','signal','pos','pnl'])
        w.writeheader()
        prev_mid = None
        for r in rd:
            sig = float(r.get(signal_col, 0.0))
            mid = float(r.get('mid', 0.0))
            if prev_mid is None: prev_mid = mid
            # latency impact (slippage approx.): move mid by small random scaled by latency and spread
            slip = float(r.get('spread',0.0))*0.25 + (latency_ms/1000.0)*0.1
            exec_price = mid + (slip if sig>thr else -slip if sig<-thr else 0.0)
            # enter/exit
            if sig > thr and pos<=0:
                pos = 1; entries += 1; pnl -= fee_bps*1e-4*exec_price
            elif sig < -thr and pos>=0:
                pos = -1; entries += 1; pnl -= fee_bps*1e-4*exec_price
            # mark-to-market
            pnl += pos*(mid - prev_mid)
            # exit on small reversal
            if abs(sig) < 0.02 and pos!=0:
                pnl -= fee_bps*1e-4*exec_price; pos = 0; exits += 1
            w.writerow({'ts': r.get('ts',''), 'signal': sig, 'pos': pos, 'pnl': pnl})
            prev_mid = mid
    print(f"[SIM] pnl={pnl:.4f}, entries={entries}, exits={exits}")
    return pnl

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--features', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--latency-ms', type=int, default=50)
    ap.add_argument('--fee-bps', type=float, default=2.0)
    ap.add_argument('--signal-col', default='microprice_imb')
    ap.add_argument('--thr', type=float, default=0.1)
    a = ap.parse_args()
    simulate(a.features, a.out, a.latency_ms, a.fee_bps, a.signal_col, a.thr)

if __name__ == '__main__':
    main()
