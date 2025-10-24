
import re

def parse_incremental(line: str, accum: dict):
    # features ΔPnL
    m = re.search(r"([+−\-])\s*([a-zA-Z0-9_]+):\s*ΔPnL\s*=\s*([\-0-9.]+)", line)
    if m:
        sign, name, val = m.group(1), m.group(2), float(m.group(3))
        feats = accum.setdefault("features", [])
        feats.append((name, val, sign))
        return
    # symbol header
    m = re.search(r"===\s*([A-Z]+)\s*===", line)
    if m:
        accum["last_symbol"] = m.group(1)
        return
    # trades/capital
    m = re.search(r"Transakcji:\s*(\d+),\s*końcowy kapitał:\s*([0-9.]+)", line)
    if m and accum.get("last_symbol"):
        sym = accum["last_symbol"]
        accum[f"{sym}_trades"] = int(m.group(1))
        accum[f"{sym}_cap"] = float(m.group(2))

def parse_full(text: str):
    acc = {}
    for ln in text.splitlines():
        parse_incremental(ln, acc)
    feats = acc.pop("features", [])
    return acc, feats
