"""Automatyczne dostrajanie kluczowych parametrów strategii."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from elbotto.backtest.engine import Backtester, BacktestReport
from elbotto.core.config import StrategyConfig
from elbotto.data.orderbook import OrderBookSeries


@dataclass(slots=True)
class EvaluationResult:
    decision_threshold: float
    max_position: float
    training_ratio: float
    final_equity: float
    total_pnl: float
    max_drawdown: float


@dataclass(slots=True)
class AutoTuneResult:
    """Wynik automatycznej kalibracji."""

    best_config: StrategyConfig
    best_score: float
    evaluations: List[EvaluationResult]


def auto_calibrate(
    series_map: Dict[str, OrderBookSeries],
    base_config: StrategyConfig,
    thresholds: Iterable[float] | None = None,
    max_positions: Iterable[float] | None = None,
    training_ratios: Iterable[float] | None = None,
) -> AutoTuneResult:
    """Przeszukuje niewielką siatkę parametrów w poszukiwaniu lepszych ustawień."""

    thresholds_list = _sanitize_candidates(
        thresholds,
        fallback=[base_config.decision_threshold * 0.95, base_config.decision_threshold, base_config.decision_threshold * 1.05],
        lower=0.51,
        upper=0.95,
    )
    positions_list = _sanitize_candidates(
        max_positions,
        fallback=[base_config.max_position * 0.8, base_config.max_position, base_config.max_position * 1.2],
        lower=0.2,
        upper=2.0,
    )
    ratios_list = _sanitize_candidates(
        training_ratios,
        fallback=[0.6, base_config.training_ratio, 0.75],
        lower=0.5,
        upper=0.9,
    )

    evaluations: List[EvaluationResult] = []
    best_score = float("-inf")
    best_config = base_config

    for threshold in thresholds_list:
        for max_position in positions_list:
            for ratio in ratios_list:
                candidate = base_config.clone_with(
                    decision_threshold=threshold,
                    max_position=max_position,
                    training_ratio=ratio,
                )
                reports = Backtester(candidate).run(series_map)
                score, summary = _score_reports(
                    reports,
                    decision_threshold=threshold,
                    max_position=max_position,
                    training_ratio=ratio,
                )
                evaluations.append(summary)
                if score > best_score:
                    best_score = score
                    best_config = candidate

    return AutoTuneResult(best_config=best_config, best_score=best_score, evaluations=evaluations)


def _sanitize_candidates(
    candidates: Iterable[float] | None,
    fallback: List[float],
    lower: float,
    upper: float,
) -> List[float]:
    values = list(candidates) if candidates is not None else fallback
    sanitized = sorted({min(max(lower, value), upper) for value in values if value > 0})
    return sanitized or [fallback[1]]


def _score_reports(
    reports: Dict[str, BacktestReport],
    *,
    decision_threshold: float,
    max_position: float,
    training_ratio: float,
) -> tuple[float, EvaluationResult]:
    total_equity = 0.0
    total_pnl = 0.0
    total_drawdown = 0.0

    for report in reports.values():
        metrics = report.state.metrics
        total_equity += metrics.get("final_equity", 0.0)
        total_pnl += metrics.get("total_pnl", 0.0)
        total_drawdown += metrics.get("max_drawdown", 0.0)

    if not reports:
        return (
            float("-inf"),
            EvaluationResult(decision_threshold, max_position, training_ratio, 0.0, 0.0, 0.0),
        )

    summary = EvaluationResult(
        decision_threshold=decision_threshold,
        max_position=max_position,
        training_ratio=training_ratio,
        final_equity=total_equity,
        total_pnl=total_pnl,
        max_drawdown=total_drawdown,
    )

    score = total_pnl - total_drawdown * 0.5
    return score, summary
