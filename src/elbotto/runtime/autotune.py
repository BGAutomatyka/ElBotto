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
    profit_spot_ratio: float
    strong_signal_multiplier: float
    probe_ratio: float
    final_equity: float
    trading_capital: float
    spot_saved: float
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
    spot_ratios: Iterable[float] | None = None,
    strong_multipliers: Iterable[float] | None = None,
    probe_ratios: Iterable[float] | None = None,
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
    spot_list = _sanitize_candidates(
        spot_ratios,
        fallback=[max(base_config.profit_spot_ratio * 0.8, 0.2), base_config.profit_spot_ratio, min(base_config.profit_spot_ratio * 1.2, 0.9)],
        lower=0.05,
        upper=0.95,
    )
    multiplier_list = _sanitize_candidates(
        strong_multipliers,
        fallback=[1.0, base_config.strong_signal_multiplier, min(base_config.strong_signal_multiplier * 1.2, 2.5)],
        lower=1.0,
        upper=3.0,
    )
    probe_list = _sanitize_candidates(
        probe_ratios,
        fallback=[max(base_config.probe_ratio * 0.8, 0.05), base_config.probe_ratio, min(base_config.probe_ratio * 1.2, 0.35)],
        lower=0.02,
        upper=0.5,
    )

    evaluations: List[EvaluationResult] = []
    best_score = float("-inf")
    best_config = base_config

    for threshold in thresholds_list:
        for max_position in positions_list:
            for ratio in ratios_list:
                for spot_ratio in spot_list:
                    for multiplier in multiplier_list:
                        for probe in probe_list:
                            candidate = base_config.clone_with(
                                decision_threshold=threshold,
                                max_position=max_position,
                                training_ratio=ratio,
                                profit_spot_ratio=spot_ratio,
                                strong_signal_multiplier=multiplier,
                                probe_ratio=probe,
                            )
                            reports = Backtester(candidate).run(series_map)
                            score, summary = _score_reports(
                                reports,
                                decision_threshold=threshold,
                                max_position=max_position,
                                training_ratio=ratio,
                                profit_spot_ratio=spot_ratio,
                                strong_signal_multiplier=multiplier,
                                probe_ratio=probe,
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
    profit_spot_ratio: float,
    strong_signal_multiplier: float,
    probe_ratio: float,
) -> tuple[float, EvaluationResult]:
    total_equity = 0.0
    trading_capital = 0.0
    spot_saved = 0.0
    total_pnl = 0.0
    total_drawdown = 0.0

    for report in reports.values():
        metrics = report.state.metrics
        total_equity += metrics.get("final_equity", 0.0)
        trading_capital += metrics.get("trading_capital", metrics.get("final_equity", 0.0))
        spot_saved += metrics.get("spot_saved", 0.0)
        total_pnl += metrics.get("total_pnl", 0.0)
        total_drawdown += metrics.get("max_drawdown", 0.0)

    if not reports:
        return (
            float("-inf"),
            EvaluationResult(
                decision_threshold,
                max_position,
                training_ratio,
                profit_spot_ratio,
                strong_signal_multiplier,
                probe_ratio,
                0.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ),
        )

    summary = EvaluationResult(
        decision_threshold=decision_threshold,
        max_position=max_position,
        training_ratio=training_ratio,
        profit_spot_ratio=profit_spot_ratio,
        strong_signal_multiplier=strong_signal_multiplier,
        probe_ratio=probe_ratio,
        final_equity=total_equity,
        trading_capital=trading_capital,
        spot_saved=spot_saved,
        total_pnl=total_pnl,
        max_drawdown=total_drawdown,
    )

    score = total_pnl - total_drawdown * 0.5 + spot_saved * 0.1
    return score, summary
