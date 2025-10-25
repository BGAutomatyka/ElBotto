import argparse, time, json, csv, statistics
from pathlib import Path
from collections import deque

def classify(rv, spread_p, ofi_var):
    if rv > 2.0 or ofi_var > 1.0: return "high_vol"
    if spread_p > 0.8: return "illiquid"
    if rv < 0.5 and ofi_var < 0.2: return "calm"
    return "trending"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="feat_csv", required=True)
    ap.add_argument("--out", dest="out_json", default="results/regime_state.json")
    ap.add_argument("--window", type=int, default=300, help="rolling window (rows)")
    a = ap.parse_args()

    rows = []
    with open(a.feat_csv, "r", encoding="utf-8") as f:
        rd = csv.DictReader(f)
        for r in rd: rows.append(r)
    mid = [float(r.get("mid",0)) for r in rows]
    spread = [float(r.get("spread",0)) for r in rows]
    ofi = [float(r.get("ofi",0)) for r in rows]

    out = Path(a.out_json); out.parent.mkdir(exist_ok=True, parents=True)
    rv = []; ofivar = []
    for i in range(1,len(mid)):
        ret = (mid[i]-mid[i-1])/(mid[i-1]+1e-9)
        rv.append(ret*ret)
        ofivar.append((ofi[i]-ofi[i-1])**2)
    def pct(v):
        if not v: return 0.0
        x = sorted(v); return x[int(0.8*(len(x)-1))]
    state = {
        "rv": sum(rv[-a.window:])/max(1,len(rv[-a.window:])),
        "spread_p80": pct(spread[-a.window:]),
        "ofi_var": sum(ofivar[-a.window:])/max(1,len(ofivar[-a.window:])),
    }
    state["regime"] = classify(state["rv"], state["spread_p80"], state["ofi_var"])
    out.write_text(json.dumps(state, indent=2), encoding="utf-8")
    print("[REGIME]", state)

if __name__ == "__main__":
    main()
