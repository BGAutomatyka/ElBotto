import re
from typing import List
from datetime import datetime

TRADE_PATTERNS = [
    re.compile(r"TRADE[: ]+time=(?P<time>[^,]+),\s*symbol=(?P<symbol>\w+),\s*side=(?P<side>BUY|SELL),\s*qty=(?P<qty>[0-9.]+),\s*price=(?P<price>[0-9.]+),\s*pnl=(?P<pnl>[-0-9.]+)", re.I),
    re.compile(r"Trade\s+(?P<symbol>\w+)\s+(?P<side>BUY|SELL)\s+qty=(?P<qty>[0-9.]+)\s+@\s+(?P<price>[0-9.]+).*?pnl=(?P<pnl>[-0-9.]+)", re.I),
]

def parse_incremental(line: str, accum: dict):
    m = re.search(r"([+−\-])\s*([a-zA-Z0-9_]+):\s*ΔPnL\s*=\s*([\-0-9.]+)", line)
    if m:
        sign, name, val = m.group(1), m.group(2), float(m.group(3))
        feats = accum.setdefault("features", []); feats.append((name, val, sign)); return
    m = re.search(r"===\s*([A-Z]+)\s*===", line)
    if m:
        accum["last_symbol"] = m.group(1); return
    m = re.search(r"Transakcji:\s*(\d+),\s*końcowy kapitał:\s*([0-9.]+)", line)
    if m and accum.get("last_symbol"):
        sym = accum["last_symbol"]; accum[f"{sym}_trades"]=int(m.group(1)); accum[f"{sym}_cap"]=float(m.group(2)); return
    for pat in TRADE_PATTERNS:
        tm = pat.search(line)
        if tm:
            tr = {"time": tm.groupdict().get("time",""), "symbol": tm.group("symbol"), "side": tm.group("side").upper(), "qty": float(tm.group("qty") or 0), "price": float(tm.group("price") or 0), "pnl": float(tm.group("pnl") or 0)}
            trades = accum.setdefault("trades", []); trades.append(tr); return

def parse_full(text: str):
    acc = {}
    for ln in text.splitlines():
        parse_incremental(ln, acc)
    feats = acc.pop("features", [])
    return acc, feats

def compute_equity(trades: List[dict], starting_capital: float = 0.0):
    times, equity = [], []
    cap = starting_capital
    for t in trades:
        cap += float(t.get("pnl", 0.0))
        ts = t.get("time","")
        times.append(ts if ts else str(len(times)))
        equity.append(cap)
    return times, equity
