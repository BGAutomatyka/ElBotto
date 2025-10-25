import asyncio, json, csv, os, time, argparse
from pathlib import Path
from datetime import datetime
import websockets

def ensure_dirs():
    Path("data/live").mkdir(parents=True, exist_ok=True)
    Path("results").mkdir(parents=True, exist_ok=True)

def features_from_book(bids, asks):
    bid1, bid1q = bids[0]
    ask1, ask1q = asks[0]
    mid = (bid1 + ask1) / 2.0
    spread = max(0.0, ask1 - bid1)
    sumb = sum(q for _, q in bids)
    suma = sum(q for _, q in asks)
    imb = (sumb - suma) / (sumb + suma) if (sumb + suma) > 0 else 0.0
    denom = (bid1q + ask1q)
    micro = (ask1 * bid1q + bid1 * ask1q) / denom if denom > 0 else mid
    micro_imb = micro - mid
    return mid, spread, imb, micro_imb

async def ws_depth(symbol: str, levels: int, q: asyncio.Queue):
    url = f"wss://stream.binance.com:9443/ws/{symbol.lower()}@depth{levels}@100ms"
    while True:
        try:
            print("[WS] connecting:", url)
            async with websockets.connect(url, ping_interval=15, ping_timeout=20) as ws:
                print("[WS] connected")
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    # obsłuż oba formaty (czasem jest data:{bids,asks})
                    payload = data.get("data", data)
                    bids_raw = payload.get("bids")
                    asks_raw = payload.get("asks")
                    if not bids_raw or not asks_raw:
                        continue
                    bids = [[float(p), float(q)] for p, q in bids_raw[:levels]]
                    asks = [[float(p), float(q)] for p, q in asks_raw[:levels]]
                    t_ms = int(payload.get("E") or time.time() * 1000)
                    await q.put((t_ms, bids, asks))
        except Exception as e:
            print("[WS] reconnect in 2s:", e)
            await asyncio.sleep(2)

def read_overrides():
    thr, risk, maxpos = 0.10, 0.005, 1
    try:
        d = json.loads(Path("results/runtime_overrides.json").read_text(encoding="utf-8"))
        thr = float(d.get("threshold", thr))
        risk = float(d.get("risk_per_trade", risk))
        maxpos = int(d.get("max_position", maxpos))
    except Exception:
        pass
    return thr, risk, maxpos

async def live_loop(q: asyncio.Queue, symbol: str, levels: int):
    feat_path = Path("results/lob_features_live.csv")
    eq_path = Path("results/equity_paper.csv")
    if not feat_path.exists():
        with feat_path.open("w", newline="") as f:
            csv.writer(f).writerow(["ts", "mid", "spread", "imbalance", "microprice_imb"])
    if not eq_path.exists():
        with eq_path.open("w", newline="") as f:
            csv.writer(f).writerow(["ts", "mid", "signal", "pos", "equity", "thr", "risk"])

    prev_mid = None
    equity = 0.0
    pos = 0

    # mały „ticker” do rotacji surowego LOB-a (opcjonalnie, godzinne pliki)
    current_hour = None
    lob_file = None
    lob_writer = None

    while True:
        t_ms, bids, asks = await q.get()
        mid, spread, imb, micro_imb = features_from_book(bids, asks)

        # zapisz featury (ciągły CSV)
        with feat_path.open("a", newline="") as f:
            csv.writer(f).writerow([t_ms, mid, spread, imb, micro_imb])

        # prosty sygnał i paper
        thr, risk, maxpos = read_overrides()
        sig = 1 if micro_imb > thr else (-1 if micro_imb < -thr else 0)

        # aktualizacja pozycji (skokowo, do +/- maxpos)
        if sig > 0 and pos < maxpos:
            pos += 1
        elif sig < 0 and pos > -maxpos:
            pos -= 1

        if prev_mid is not None:
            equity += pos * (mid - prev_mid)
        prev_mid = mid

        with eq_path.open("a", newline="") as f:
            csv.writer(f).writerow([t_ms, mid, sig, pos, equity, thr, risk])

        # (opcjonalnie) surowy LOB per godzina
        dt = datetime.utcfromtimestamp(t_ms / 1000)
        hour_tag = dt.strftime("%Y%m%d_%H")
        if hour_tag != current_hour:
            current_hour = hour_tag
            if lob_file:
                lob_file.close()
            raw_path = Path(f"data/live/{symbol.upper()}_depth{levels}_{hour_tag}.csv")
            lob_file = raw_path.open("a", newline="")
            lob_writer = csv.writer(lob_file)
            if raw_path.stat().st_size == 0:
                header = ["ts"] + \
                         [f"bid{i+1}" for i in range(levels)] + \
                         [f"bid{i+1}_qty" for i in range(levels)] + \
                         [f"ask{i+1}" for i in range(levels)] + \
                         [f"ask{i+1}_qty" for i in range(levels)]
                lob_writer.writerow(header)
        if lob_writer:
            row = [t_ms] + \
                  [p for p, _ in bids] + [q for _, q in bids] + \
                  [p for p, _ in asks] + [q for _, q in asks]
            lob_writer.writerow(row)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="BTCUSDT")
    parser.add_argument("--levels", type=int, default=10)
    args = parser.parse_args()

    ensure_dirs()
    q = asyncio.Queue(maxsize=2000)
    await asyncio.gather(
        ws_depth(args.symbol, args.levels, q),
        live_loop(q, args.symbol, args.levels)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[EXIT] bye")
