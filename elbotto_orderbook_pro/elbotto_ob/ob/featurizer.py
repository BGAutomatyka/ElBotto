from __future__ import annotations
import argparse, csv, math
from pathlib import Path
from typing import List, Dict

def microprice(b1, a1, q_bid, q_ask):
    if (q_bid+q_ask) <= 0: return (b1+a1)/2.0
    return (a1*q_bid + b1*q_ask)/(q_bid+q_ask)

def book_slope(levels: List[Dict[str,float]]):
    # linear fit of price vs cum_qty on bid/ask separately, return slope diff
    import numpy as np
    bids = [(l['bid_price'], l['bid_qty']) for l in levels if l['bid_qty']>0]
    asks = [(l['ask_price'], l['ask_qty']) for l in levels if l['ask_qty']>0]
    def slope(pairs):
        if len(pairs) < 2: return 0.0
        px = np.array([p for p,_ in pairs], dtype=float)
        q  = np.array([q for _,q in pairs], dtype=float).cumsum()
        X = np.vstack([q, np.ones_like(q)]).T
        m, c = np.linalg.lstsq(X, px, rcond=None)[0]
        return float(m)
    return slope(bids) - slope(asks)

def compute_features(rows: List[Dict[str,str]], levels=10):
    out = []
    for r in rows:
        b1 = float(r.get('bid1', r.get('best_bid', 0.0))); a1 = float(r.get('ask1', r.get('best_ask', 0.0)))
        mid = (b1+a1)/2.0; spread = max(0.0, a1-b1)
        q_bid = float(r.get('bid1_qty', r.get('bid_qty1', 0.0))); q_ask = float(r.get('ask1_qty', r.get('ask_qty1', 0.0)))
        mp = microprice(b1,a1,q_bid,q_ask)
        # depth imbalance (top-N)
        bsum = 0.0; asum = 0.0
        for i in range(1, levels+1):
            bsum += float(r.get(f'bid{i}_qty', r.get(f'bid_qty{i}', 0.0)) or 0.0)
            asum += float(r.get(f'ask{i}_qty', r.get(f'ask_qty{i}', 0.0)) or 0.0)
        dib = (bsum - asum) / (bsum + asum + 1e-9)
        # queue imbalance top1
        q_imb = (q_bid - q_ask) / (q_bid + q_ask + 1e-9)
        # microprice imbalance
        mp_imb = (mp - mid) / (spread + 1e-9)
        # order flow imbalance (naive, requires last trade volumes – if absent, use delta top qty)
        ofi = float(r.get('ofi', 0.0))
        # book slope diff
        lvl = []
        for i in range(1, min(levels,5)+1):
            lvl.append({
                'bid_price': float(r.get(f'bid{i}', r.get(f'bid_price{i}', b1)) or b1),
                'bid_qty': float(r.get(f'bid{i}_qty', r.get(f'bid_qty{i}', 0.0)) or 0.0),
                'ask_price': float(r.get(f'ask{i}', r.get(f'ask_price{i}', a1)) or a1),
                'ask_qty': float(r.get(f'ask{i}_qty', r.get(f'ask_qty{i}', 0.0)) or 0.0),
            })
        slope = book_slope(lvl) if lvl else 0.0
        out.append({
            'ts': r.get('ts', r.get('timestamp', '')),
            'mid': mid, 'spread': spread, 'microprice': mp, 'microprice_imb': mp_imb,
            'q_imb': q_imb, 'depth_imbalance': dib, 'ofi': ofi, 'book_slope': slope
        })
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--in', dest='infile', required=True, help='CSV z L2/L3 (kolumny: bid1,ask1,bid1_qty,ask1_qty, ... )')
    ap.add_argument('--out', dest='outfile', required=True, help='CSV z cechami')
    ap.add_argument('--levels', type=int, default=10)
    ap.add_argument('--agg-sec', type=int, default=1, help='agregacja do n sekund (opcjonalnie)')
    args = ap.parse_args()

    rows = []
    with open(args.infile, 'r', encoding='utf-8') as f:
        rd = csv.DictReader(f)
        for r in rd:
            rows.append(r)
    feats = compute_features(rows, levels=args.levels)
    with open(args.outfile, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(feats[0].keys()))
        w.writeheader(); w.writerows(feats)
    print("[OB] wrote", args.outfile)

if __name__ == '__main__':
    main()
