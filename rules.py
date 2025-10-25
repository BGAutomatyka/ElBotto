from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any
import json, time
from pathlib import Path

@dataclass
class Rule:
    name: str
    symbols: List[str]  # empty = any
    include_any: List[str]
    include_all: List[str]
    exclude_any: List[str]
    min_sent: float | None  # -1..1
    action: Dict[str, Any]  # e.g. {"threshold_delta": -0.05, "risk_mult": 0.5, "pause_sec": 120}
    ttl_sec: int

def load_rules(path: Path) -> List[Rule]:
    if not path.exists(): return []
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: List[Rule] = []
    for r in raw.get("rules", []):
        out.append(Rule(
            name=r.get("name","rule"),
            symbols=r.get("symbols",[]),
            include_any=[w.lower() for w in r.get("include_any",[])],
            include_all=[w.lower() for w in r.get("include_all",[])],
            exclude_any=[w.lower() for w in r.get("exclude_any",[])],
            min_sent=r.get("min_sent", None),
            action=r.get("action",{}),
            ttl_sec=int(r.get("ttl_sec", 600))
        ))
    return out

def match_rule(rule: Rule, item: Dict[str, Any]) -> bool:
    text = (item.get("title","") + " " + " ".join(item.get("symbols",[]))).lower()
    if rule.symbols:
        if not any(sym in item.get("symbols",[]) for sym in rule.symbols):
            return False
    if rule.include_any and not any(w in text for w in rule.include_any):
        return False
    if rule.include_all and not all(w in text for w in rule.include_all):
        return False
    if rule.exclude_any and any(w in text for w in rule.exclude_any):
        return False
    if rule.min_sent is not None and float(item.get("sentiment",0.0)) < float(rule.min_sent):
        return False
    return True

def apply_action(base: Dict[str, Any], action: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    if "threshold_delta" in action:
        out["threshold"] = round(max(0.1, min(0.9, float(out.get("threshold",0.5)) + float(action["threshold_delta"]))), 3)
    if "threshold_set" in action:
        out["threshold"] = float(action["threshold_set"])
    if "risk_mult" in action:
        r = float(out.get("risk_per_trade", 0.01) or 0.01) * float(action["risk_mult"])
        out["risk_per_trade"] = round(max(0.001, min(0.05, r)), 4)
    if "maxpos_mult" in action:
        mp = float(out.get("max_position", 1.0) or 1.0) * float(action["maxpos_mult"])
        out["max_position"] = round(max(0.2, min(3.0, mp)), 2)
    if "pause_sec" in action:
        out["pause_until"] = time.time() + int(action["pause_sec"])
    return out
