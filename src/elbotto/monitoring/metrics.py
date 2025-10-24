"""Proste miary bezpieczeństwa i kontroli wyników."""

from __future__ import annotations

from typing import Dict


def evaluate_safety(metrics: Dict[str, float], risk_limits: Dict[str, float]) -> bool:
    """Sprawdza czy metryki mieszczą się w zadanych limitach."""

    for key, limit in risk_limits.items():
        value = metrics.get(key)
        if value is None:
            continue
        if key.endswith("_max") and value > limit:
            return False
        if key.endswith("_min") and value < limit:
            return False
    return True
