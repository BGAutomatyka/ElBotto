
import re
from typing import Tuple, List, Dict

def parse_incremental(line: str, accum: Dict) -> None:
    """Update metrics/features from a single output line."""
    # Feature importances line
    m = re.search(r"([+−\-])\s*([a-zA-Z0-9_]+):\s*ΔPnL\s*=\s*([\-0-9.]+)", line)
    if m:
        sign, name, val = m.group(1), m.group(2), float(m.group(3))
        feats = accum.setdefault("features", [])
        feats.append((name, val, sign))
        return
    # Trades & capital line (after symbol header)
    m2 = re.search(r"Transakcji:\s*(\d+),\s*końcowy kapitał:\s*([0-9.]+)", line)
    if m2 and accum.get("last_symbol"):
        sym = accum["last_symbol"]
        trades, cap = int(m2.group(1)), float(m2.group(2))
        accum[f"{sym}_trades"] = trades
        accum[f"{sym}_cap"] = cap
        return
    # Symbol header
    m3 = re.search(r"===\s*([A-Z]+)\s*===", line)
    if m3:
        accum["last_symbol"] = m3.group(1)

def parse_full(text: str):
    """Parse a whole log into metrics and features."""
    accum = {}
    for ln in text.splitlines():
        parse_incremental(ln, accum)
    feats = accum.pop("features", [])
    # map to flat metrics
    metrics = {}
    for k,v in accum.items():
        metrics[k] = v
    return metrics, feats
