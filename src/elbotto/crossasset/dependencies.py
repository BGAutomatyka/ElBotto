"""Analiza zależności między parami na bazie rzeczywistych danych."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean
from typing import Dict, List

from elbotto.data.orderbook import OrderBookSeries


@dataclass(slots=True)
class DependencyResult:
    symbol_a: str
    symbol_b: str
    correlation: float
    lead_lag: int


def _mid_prices(series: OrderBookSeries) -> List[float]:
    return [(sample.bid_price_1 + sample.ask_price_1) / 2 for sample in series.samples]


def _correlation(a: List[float], b: List[float]) -> float:
    if len(a) != len(b) or len(a) < 2:
        return 0.0
    mean_a = mean(a)
    mean_b = mean(b)
    cov = sum((x - mean_a) * (y - mean_b) for x, y in zip(a, b))
    var_a = sum((x - mean_a) ** 2 for x in a)
    var_b = sum((y - mean_b) ** 2 for y in b)
    denom = (var_a * var_b) ** 0.5
    return cov / denom if denom else 0.0


def analyse_dependencies(series_map: Dict[str, OrderBookSeries], max_lag: int = 10) -> List[DependencyResult]:
    symbols = sorted(series_map)
    results: List[DependencyResult] = []
    for i, sym_a in enumerate(symbols):
        prices_a = _mid_prices(series_map[sym_a])
        for sym_b in symbols[i + 1 :]:
            prices_b = _mid_prices(series_map[sym_b])
            min_len = min(len(prices_a), len(prices_b))
            if min_len < 2:
                continue
            a = prices_a[-min_len:]
            b = prices_b[-min_len:]
            corr = _correlation(a, b)
            best_lag = 0
            best_score = 0.0
            for lag in range(-max_lag, max_lag + 1):
                if lag < 0:
                    shifted_a = a[:lag]
                    shifted_b = b[-lag:]
                elif lag > 0:
                    shifted_a = a[lag:]
                    shifted_b = b[:-lag]
                else:
                    shifted_a = a
                    shifted_b = b
                if len(shifted_a) < 2:
                    continue
                score = _correlation(shifted_a, shifted_b)
                if abs(score) > abs(best_score):
                    best_score = score
                    best_lag = lag
            results.append(
                DependencyResult(
                    symbol_a=sym_a,
                    symbol_b=sym_b,
                    correlation=corr,
                    lead_lag=best_lag,
                )
            )
    return results
