"""Wyliczanie cech mikrostruktury księgi zleceń bez bibliotek zewnętrznych."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import pstdev
from typing import Dict, List, Sequence, Tuple

from elbotto.data.orderbook import OrderBookSample, OrderBookSeries


@dataclass(slots=True)
class FeatureMatrix:
    features: List[List[float]]
    target: List[float]
    spread: List[float]
    timestamps: List[str]
    feature_names: Tuple[str, ...]


def _microprice(sample: OrderBookSample) -> float:
    total = sample.bid_size_1 + sample.ask_size_1
    if total == 0:
        return (sample.bid_price_1 + sample.ask_price_1) / 2
    return (sample.ask_price_1 * sample.bid_size_1 + sample.bid_price_1 * sample.ask_size_1) / total


def _imbalance(sample: OrderBookSample) -> float:
    total = sample.bid_size_1 + sample.ask_size_1
    if total == 0:
        return 0.0
    return (sample.bid_size_1 - sample.ask_size_1) / total


def _rolling_std(values: List[float], window: int) -> List[float]:
    result: List[float] = []
    for idx in range(len(values)):
        start = max(0, idx - window + 1)
        segment = values[start : idx + 1]
        if len(segment) < 2:
            result.append(0.0)
        else:
            result.append(pstdev(segment))
    return result


def build_feature_matrix(series: OrderBookSeries, horizon: int = 5) -> FeatureMatrix:
    if horizon <= 0:
        raise ValueError("horizon musi być dodatni")

    bids_1 = [sample.bid_price_1 for sample in series.samples]
    asks_1 = [sample.ask_price_1 for sample in series.samples]
    bids_2 = [sample.bid_price_2 for sample in series.samples]
    asks_2 = [sample.ask_price_2 for sample in series.samples]
    bid_sizes = [sample.bid_size_1 + sample.bid_size_2 for sample in series.samples]
    ask_sizes = [sample.ask_size_1 + sample.ask_size_2 for sample in series.samples]
    volumes = [sample.trade_volume for sample in series.samples]

    mids = [(bid + ask) / 2 for bid, ask in zip(bids_1, asks_1)]
    spread = [ask - bid for bid, ask in zip(bids_1, asks_1)]
    microprices = [_microprice(sample) for sample in series.samples]
    imbalance = [_imbalance(sample) for sample in series.samples]

    delta_mid = [0.0]
    delta_mid.extend(m2 - m1 for m1, m2 in zip(mids, mids[1:]))
    delta_volume = [0.0]
    delta_volume.extend(v2 - v1 for v1, v2 in zip(volumes, volumes[1:]))
    rolling_std = _rolling_std(delta_mid, 5)

    feature_rows: List[List[float]] = []
    for idx in range(len(series.samples)):
        feature_rows.append(
            [
                mids[idx],
                spread[idx],
                microprices[idx] - mids[idx],
                imbalance[idx],
                bid_sizes[idx] - ask_sizes[idx],
                delta_mid[idx],
                delta_volume[idx],
                rolling_std[idx],
            ]
        )

    future_mid = mids[horizon:] + [mids[-1]] * horizon
    target = [1.0 if f > c else 0.0 for c, f in zip(mids, future_mid)]
    for idx in range(len(target) - horizon, len(target)):
        target[idx] = 0.5

    timestamps = [sample.timestamp.isoformat() for sample in series.samples]
    feature_names = (
        "mid",
        "spread",
        "microprice_edge",
        "imbalance",
        "queue_pressure",
        "delta_mid",
        "delta_volume",
        "rolling_vol",
    )

    return FeatureMatrix(
        features=feature_rows,
        target=target,
        spread=spread,
        timestamps=timestamps,
        feature_names=feature_names,
    )


def compute_event_windows(series: OrderBookSeries, window_sizes: Sequence[int]) -> Dict[int, float]:
    mids = [(sample.bid_price_1 + sample.ask_price_1) / 2 for sample in series.samples]
    result: Dict[int, float] = {}
    for size in window_sizes:
        if size <= 1 or size > len(mids):
            continue
        grouped = [mids[i : i + size] for i in range(0, len(mids) - size + 1, size)]
        if not grouped:
            continue
        window_returns = [group[-1] - group[0] for group in grouped]
        result[size] = pstdev(window_returns) if len(window_returns) > 1 else 0.0
    return result
