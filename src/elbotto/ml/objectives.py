"""Funkcje celu bez zależności zewnętrznych."""

from __future__ import annotations

import math
from typing import Iterable, List


def logistic_cost(pred: Iterable[float], target: Iterable[float], weights: Iterable[float] | None = None) -> float:
    preds = list(pred)
    targets = list(target)
    if weights is None:
        weights_list = [1.0] * len(preds)
    else:
        weights_list = list(weights)
    eps = 1e-9
    total_weight = sum(weights_list)
    loss = 0.0
    for p, t, w in zip(preds, targets, weights_list):
        p = min(max(p, eps), 1 - eps)
        loss += w * (-(t * math.log(p) + (1 - t) * math.log(1 - p)))
    return loss / total_weight if total_weight else 0.0


def cost_weights(spread: Iterable[float], fee_rate: float) -> List[float]:
    weights: List[float] = []
    for sp in spread:
        edge = max(sp / 2 - fee_rate, 0)
        weights.append(1 + edge / (fee_rate + 1e-6))
    return weights
