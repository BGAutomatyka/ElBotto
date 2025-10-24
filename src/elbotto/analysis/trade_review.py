"""Wnioski z przebytych transakcji i rekomendacje usprawnień."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from elbotto.analysis.diagnostics import FeatureEffect, ImpactReport
from elbotto.backtest.engine import BacktestReport


@dataclass(slots=True)
class AdjustmentSuggestion:
    """Sugestia zmiany konfiguracji na podstawie historii transakcji."""

    parameter: str
    suggested_value: float
    rationale: str


@dataclass(slots=True)
class TradeReview:
    """Skondensowane wnioski z backtestu i analizy cech."""

    total_trades: int
    total_pnl: float
    total_fees: float
    average_trade_notional: float
    max_notional: float
    loss_drivers: List[FeatureEffect]
    gain_drivers: List[FeatureEffect]
    suggestions: List[AdjustmentSuggestion]


def review_trades(
    reports: Dict[str, BacktestReport],
    impacts: ImpactReport | None,
) -> TradeReview:
    """Tworzy syntetyczny raport o tym, co działa, a co szkodzi strategii."""

    total_trades = 0
    total_pnl = 0.0
    total_fees = 0.0
    total_notional = 0.0
    max_notional = 0.0

    for report in reports.values():
        total_trades += report.state.metrics.get("trade_count", 0)
        total_pnl += report.state.metrics.get("total_pnl", 0.0)
        total_fees += report.state.metrics.get("total_fees", 0.0)
        total_notional += report.state.metrics.get("average_trade_size_usd", 0.0) * report.state.metrics.get("trade_count", 0)
        max_notional = max(max_notional, report.state.metrics.get("max_notional_usd", 0.0))

    avg_notional = total_notional / total_trades if total_trades else 0.0
    loss_drivers = impacts.loss_drivers(top_n=3) if impacts else []
    gain_drivers = impacts.gain_drivers(top_n=3) if impacts else []
    suggestions = _suggest_adjustments(loss_drivers, gain_drivers, total_pnl)

    return TradeReview(
        total_trades=total_trades,
        total_pnl=total_pnl,
        total_fees=total_fees,
        average_trade_notional=avg_notional,
        max_notional=max_notional,
        loss_drivers=loss_drivers,
        gain_drivers=gain_drivers,
        suggestions=suggestions,
    )


def _suggest_adjustments(
    losses: List[FeatureEffect],
    gains: List[FeatureEffect],
    total_pnl: float,
) -> List[AdjustmentSuggestion]:
    """Buduje listę rekomendacji, aby ograniczyć straty i wzmacniać zyski."""

    suggestions: List[AdjustmentSuggestion] = []
    baseline_threshold = 0.6 if total_pnl <= 0 else 0.55

    for effect in losses:
        feature = effect.feature.lower()
        if "vpin" in feature:
            suggestions.append(
                AdjustmentSuggestion(
                    parameter="risk.max_vpin",
                    suggested_value=0.5,
                    rationale="Wysoka toksyczność (VPIN) zwiększa prawdopodobieństwo strat – zaostrzenie limitu zabezpieczy wejścia.",
                )
            )
        elif "spread" in feature:
            suggestions.append(
                AdjustmentSuggestion(
                    parameter="decision_threshold",
                    suggested_value=max(baseline_threshold, 0.6),
                    rationale="Straty pojawiały się przy szerokim spreadzie – podniesienie progu pewności ograniczy handel w gorszych warunkach.",
                )
            )
        elif "queue" in feature or "imbalance" in feature:
            suggestions.append(
                AdjustmentSuggestion(
                    parameter="max_position",
                    suggested_value=0.6,
                    rationale="Niekorzystna presja zleceń sugeruje, by zmniejszyć maksymalny rozmiar pozycji.",
                )
            )

    if total_pnl < 0:
        suggestions.append(
            AdjustmentSuggestion(
                parameter="training_ratio",
                suggested_value=0.7,
                rationale="Ujemny wynik netto – warto zwiększyć część danych treningowych, aby model był bardziej stabilny.",
            )
        )

    if not suggestions and gains:
        top_gain = gains[0]
        suggestions.append(
            AdjustmentSuggestion(
                parameter="decision_threshold",
                suggested_value=baseline_threshold,
                rationale=(
                    "Kluczowy sygnał zysków to "
                    f"{top_gain.feature}. Warto utrzymać obecne ustawienia i monitorować jego wartość na żywo."
                ),
            )
        )

    return suggestions
