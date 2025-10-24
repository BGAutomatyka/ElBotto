"""Analiza wpływu wskaźników na wynik strategii."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from elbotto.backtest.engine import BacktestReport
from elbotto.data.orderbook import OrderBookSeries
from elbotto.exec.strategies.microstructure import Trade
from elbotto.microstructure.features import FeatureMatrix, build_feature_matrix


@dataclass(slots=True)
class FeatureEffect:
    """Wpływ pojedynczego wskaźnika na wynik PnL."""

    feature: str
    positive_mean: float
    negative_mean: float
    difference: float
    trade_count: int


@dataclass(slots=True)
class ImpactReport:
    """Podsumowanie wyników analizy wpływu cech."""

    per_symbol: Dict[str, List[FeatureEffect]]
    aggregated: List[FeatureEffect]

    def loss_drivers(self, top_n: int = 3) -> List[FeatureEffect]:
        """Zwraca cechy najbardziej związane ze stratami."""

        losses = [effect for effect in self.aggregated if effect.difference < 0]
        return sorted(losses, key=lambda eff: eff.difference)[:top_n]

    def gain_drivers(self, top_n: int = 3) -> List[FeatureEffect]:
        """Zwraca cechy najbardziej wspierające zysk."""

        gains = [effect for effect in self.aggregated if effect.difference > 0]
        return sorted(gains, key=lambda eff: eff.difference, reverse=True)[:top_n]


def evaluate_feature_impacts(
    series_map: Dict[str, OrderBookSeries],
    reports: Dict[str, BacktestReport],
    horizon: int = 5,
) -> ImpactReport:
    """Analizuje jak cechy wpływają na PnL w raportach backtestu."""

    per_symbol: Dict[str, List[FeatureEffect]] = {}
    aggregate_accumulator: Dict[str, Tuple[float, float, float]] = {}

    for symbol, report in reports.items():
        series = series_map.get(symbol)
        if series is None:
            continue
        matrix: FeatureMatrix = build_feature_matrix(series, horizon=horizon)
        timestamp_to_row = {timestamp: row for timestamp, row in zip(matrix.timestamps, matrix.features)}
        effects: List[FeatureEffect] = []
        trade_rows = _match_trades_with_features(report.state.trades, timestamp_to_row)
        if not trade_rows:
            trade_rows = _fallback_from_matrix(matrix)
        if not trade_rows:
            per_symbol[symbol] = effects
            continue
        for feature_idx, feature_name in enumerate(matrix.feature_names):
            values = [row[feature_idx] for row, _ in trade_rows]
            pnls = [pnl for _, pnl in trade_rows]
            positive_mean, negative_mean = _split_means(values, pnls)
            if positive_mean == 0 and negative_mean == 0:
                continue
            difference = positive_mean - negative_mean
            effect = FeatureEffect(
                feature=feature_name,
                positive_mean=positive_mean,
                negative_mean=negative_mean,
                difference=difference,
                trade_count=len(trade_rows),
            )
            effects.append(effect)
            aggregate_accumulator.setdefault(feature_name, (0.0, 0.0, 0.0))
            pos_sum, neg_sum, weight_sum = aggregate_accumulator[feature_name]
            aggregate_accumulator[feature_name] = (
                pos_sum + positive_mean * len(trade_rows),
                neg_sum + negative_mean * len(trade_rows),
                weight_sum + len(trade_rows),
            )
        per_symbol[symbol] = effects

    aggregated: List[FeatureEffect] = []
    for feature_name, (pos_sum, neg_sum, weight_sum) in aggregate_accumulator.items():
        if weight_sum == 0:
            continue
        pos_mean = pos_sum / weight_sum if weight_sum else 0.0
        neg_mean = neg_sum / weight_sum if weight_sum else 0.0
        aggregated.append(
            FeatureEffect(
                feature=feature_name,
                positive_mean=pos_mean,
                negative_mean=neg_mean,
                difference=pos_mean - neg_mean,
                trade_count=int(weight_sum),
            )
        )

    aggregated.sort(key=lambda effect: effect.difference, reverse=True)
    return ImpactReport(per_symbol=per_symbol, aggregated=aggregated)


def _match_trades_with_features(
    trades: List[Trade],
    timestamp_to_row: Dict[str, List[float]],
) -> List[Tuple[List[float], float]]:
    matched: List[Tuple[List[float], float]] = []
    for trade in trades:
        row = timestamp_to_row.get(trade.timestamp)
        if row is None:
            continue
        matched.append((row, trade.pnl))
    return matched


def _fallback_from_matrix(matrix: FeatureMatrix) -> List[Tuple[List[float], float]]:
    fallback: List[Tuple[List[float], float]] = []
    for row, target, spread in zip(matrix.features, matrix.target, matrix.spread):
        if target == 0.5:
            continue
        pnl = (target - 0.5) * spread
        fallback.append((row, pnl))
    return fallback


def _split_means(values: Iterable[float], pnls: Iterable[float]) -> Tuple[float, float]:
    pairs = list(zip(values, pnls))
    if not pairs:
        return 0.0, 0.0
    sorted_pairs = sorted(pairs, key=lambda item: item[0])
    size = len(sorted_pairs)
    lower_index = max(0, int(size * 0.25) - 1)
    upper_index = min(size - 1, int(size * 0.75))
    lower_bound = sorted_pairs[lower_index][0]
    upper_bound = sorted_pairs[upper_index][0]
    negative_bucket = [pnl for value, pnl in sorted_pairs if value <= lower_bound]
    positive_bucket = [pnl for value, pnl in sorted_pairs if value >= upper_bound]
    negative_mean = sum(negative_bucket) / len(negative_bucket) if negative_bucket else 0.0
    positive_mean = sum(positive_bucket) / len(positive_bucket) if positive_bucket else 0.0
    return positive_mean, negative_mean
