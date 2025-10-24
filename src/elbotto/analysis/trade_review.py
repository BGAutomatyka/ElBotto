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
    spot_saved: float
    trading_capital: float
    spot_ratio: float
    counterfactual_gain: float
    counterfactual_loss: float
    counterfactual_opportunities: int
    counterfactual_avoided: int
    probe_trades: int
    strong_trades: int
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
    total_spot = 0.0
    total_trading_capital = 0.0
    total_equity = 0.0
    counterfactual_gain = 0.0
    counterfactual_loss = 0.0
    counterfactual_opportunities = 0
    counterfactual_avoided = 0
    total_probe_trades = 0
    total_strong_trades = 0

    for report in reports.values():
        total_trades += report.state.metrics.get("trade_count", 0)
        total_pnl += report.state.metrics.get("total_pnl", 0.0)
        total_fees += report.state.metrics.get("total_fees", 0.0)
        total_notional += report.state.metrics.get("average_trade_size_usd", 0.0) * report.state.metrics.get("trade_count", 0)
        max_notional = max(max_notional, report.state.metrics.get("max_notional_usd", 0.0))
        total_spot += report.state.metrics.get("spot_saved", 0.0)
        total_trading_capital += report.state.metrics.get("trading_capital", 0.0)
        total_equity += report.state.metrics.get("final_equity", 0.0)
        counterfactual_gain += report.state.metrics.get("counterfactual_gain", 0.0)
        counterfactual_loss += report.state.metrics.get("counterfactual_loss", 0.0)
        counterfactual_opportunities += report.state.metrics.get("counterfactual_opportunities", 0)
        counterfactual_avoided += report.state.metrics.get("counterfactual_avoided", 0)
        total_probe_trades += report.state.metrics.get("probe_trades", 0)
        total_strong_trades += report.state.metrics.get("strong_trades", 0)

    avg_notional = total_notional / total_trades if total_trades else 0.0
    spot_ratio = total_spot / total_equity if total_equity else 0.0
    loss_drivers = impacts.loss_drivers(top_n=3) if impacts else []
    gain_drivers = impacts.gain_drivers(top_n=3) if impacts else []
    suggestions = _suggest_adjustments(
        losses=loss_drivers,
        gains=gain_drivers,
        total_pnl=total_pnl,
        spot_ratio=spot_ratio,
        counterfactual_gain=counterfactual_gain,
        counterfactual_loss=counterfactual_loss,
        counterfactual_opportunities=counterfactual_opportunities,
        counterfactual_avoided=counterfactual_avoided,
        probe_trades=total_probe_trades,
    )

    return TradeReview(
        total_trades=total_trades,
        total_pnl=total_pnl,
        total_fees=total_fees,
        average_trade_notional=avg_notional,
        max_notional=max_notional,
        spot_saved=total_spot,
        trading_capital=total_trading_capital,
        spot_ratio=spot_ratio,
        counterfactual_gain=counterfactual_gain,
        counterfactual_loss=counterfactual_loss,
        counterfactual_opportunities=counterfactual_opportunities,
        counterfactual_avoided=counterfactual_avoided,
        probe_trades=total_probe_trades,
        strong_trades=total_strong_trades,
        loss_drivers=loss_drivers,
        gain_drivers=gain_drivers,
        suggestions=suggestions,
    )


def _suggest_adjustments(
    losses: List[FeatureEffect],
    gains: List[FeatureEffect],
    total_pnl: float,
    spot_ratio: float,
    counterfactual_gain: float,
    counterfactual_loss: float,
    counterfactual_opportunities: int,
    counterfactual_avoided: int,
    probe_trades: int,
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

    if spot_ratio < 0.2 and total_pnl > 0:
        suggestions.append(
            AdjustmentSuggestion(
                parameter="profit_spot_ratio",
                suggested_value=0.6,
                rationale="Mały udział oszczędności spot – zwiększenie odkładanej części zysków poprawi ochronę kapitału.",
            )
        )
    elif spot_ratio > 0.65 and total_pnl > 0:
        suggestions.append(
            AdjustmentSuggestion(
                parameter="profit_spot_ratio",
                suggested_value=0.4,
                rationale="Większość kapitału trafia na spot – zmniejszenie udziału pozwoli na większą reinwestycję.",
            )
        )

    if counterfactual_opportunities > counterfactual_avoided and counterfactual_gain > counterfactual_loss:
        suggestions.append(
            AdjustmentSuggestion(
                parameter="decision_threshold",
                suggested_value=max(0.5, baseline_threshold - 0.02),
                rationale="Model wskazuje na niewykorzystane okazje – lekkie obniżenie progu może poprawić skuteczność.",
            )
        )
        if probe_trades < counterfactual_opportunities:
            suggestions.append(
                AdjustmentSuggestion(
                    parameter="probe_ratio",
                    suggested_value=0.2,
                    rationale="Warto zwiększyć wolumen sondujących transakcji, aby szybciej ocenić niepewne sygnały.",
                )
            )
    elif counterfactual_avoided > counterfactual_opportunities * 1.5:
        suggestions.append(
            AdjustmentSuggestion(
                parameter="min_reserve_ratio",
                suggested_value=0.25,
                rationale="Wysoka liczba unikniętych strat – podwyższenie rezerwy bezpieczeństwa zabezpieczy kapitał.",
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
