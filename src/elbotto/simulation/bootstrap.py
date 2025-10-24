"""Symulacje scenariuszy oparte na bootstrapie z realnych danych."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from elbotto.data.orderbook import OrderBookSeries


@dataclass(slots=True)
class ScenarioPoint:
    mid: float
    spread: float
    microprice: float


def bootstrap_scenarios(series: OrderBookSeries, steps: int, seed: int | None = None) -> List[ScenarioPoint]:
    if steps <= 0:
        raise ValueError("steps musi być dodatni")
    rng = random.Random(seed)
    scenario: List[ScenarioPoint] = []
    for _ in range(steps):
        sample = rng.choice(series.samples)
        mid = (sample.bid_price_1 + sample.ask_price_1) / 2
        spread = sample.ask_price_1 - sample.bid_price_1
        total = sample.bid_size_1 + sample.ask_size_1
        microprice = (
            (sample.ask_price_1 * sample.bid_size_1 + sample.bid_price_1 * sample.ask_size_1)
            / total
            if total
            else mid
        )
        scenario.append(ScenarioPoint(mid=mid, spread=spread, microprice=microprice))
    return scenario
