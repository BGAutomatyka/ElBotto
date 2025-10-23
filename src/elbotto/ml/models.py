"""Regresja logistyczna oparta na czystym Pythonie."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List

from elbotto.ml.objectives import cost_weights, logistic_cost


def _dot(row: Iterable[float], weights: List[float]) -> float:
    return sum(a * b for a, b in zip(row, weights))


def _sigmoid(value: float) -> float:
    if value >= 0:
        z = math.exp(-value)
        return 1 / (1 + z)
    z = math.exp(value)
    return z / (1 + z)


@dataclass(slots=True)
class LogisticModel:
    weights: List[float]
    bias: float

    @classmethod
    def train(
        cls,
        features: List[List[float]],
        target: List[float],
        spread: List[float],
        fee_rate: float,
        learning_rate: float = 0.05,
        epochs: int = 300,
    ) -> "LogisticModel":
        mask = [t != 0.5 for t in target]
        x = [row for row, keep in zip(features, mask) if keep]
        y = [t for t in target if t != 0.5]
        if not x:
            return cls(weights=[0.0] * len(features[0]), bias=0.0)
        w = [0.0] * len(x[0])
        b = 0.0
        weights_cost = cost_weights([s for s, keep in zip(spread, mask) if keep], fee_rate)
        for _ in range(epochs):
            grad_w = [0.0] * len(w)
            grad_b = 0.0
            for row, label, weight in zip(x, y, weights_cost):
                prediction = _sigmoid(_dot(row, w) + b)
                error = (prediction - label) * weight
                for idx, value in enumerate(row):
                    grad_w[idx] += error * value
                grad_b += error
            scale = 1 / len(x)
            w = [wi - learning_rate * scale * g for wi, g in zip(w, grad_w)]
            b -= learning_rate * scale * grad_b
        return cls(weights=w, bias=b)

    def predict_proba(self, features: List[List[float]]) -> List[float]:
        return [_sigmoid(_dot(row, self.weights) + self.bias) for row in features]

    def score(self, features: List[List[float]], target: List[float], spread: List[float], fee_rate: float) -> float:
        pred = self.predict_proba(features)
        mask = [t != 0.5 for t in target]
        filtered_pred = [p for p, keep in zip(pred, mask) if keep]
        filtered_target = [t for t in target if t != 0.5]
        filtered_spread = [s for s, keep in zip(spread, mask) if keep]
        return logistic_cost(filtered_pred, filtered_target, cost_weights(filtered_spread, fee_rate))
