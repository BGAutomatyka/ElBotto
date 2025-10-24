"""Konfiguracja bota i ograniczenia ryzyka."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List


@dataclass(slots=True)
class RiskLimits:
    """Ograniczenia bezpieczeństwa obowiązujące podczas handlu."""

    intraday_drawdown: float = 0.04
    cvar_limit: float = 0.06
    max_participation: float = 0.15
    max_vpin: float = 0.6
    slippage_budget_bps: float = 6.0

    def validate(self) -> None:
        if not 0 < self.intraday_drawdown < 1:
            raise ValueError("intraday_drawdown musi być w (0,1)")
        if not 0 < self.cvar_limit < 1:
            raise ValueError("cvar_limit musi być w (0,1)")
        if not 0 < self.max_participation <= 1:
            raise ValueError("max_participation musi być w (0,1]")
        if not 0 < self.max_vpin < 1:
            raise ValueError("max_vpin musi być w (0,1)")
        if self.slippage_budget_bps <= 0:
            raise ValueError("slippage_budget_bps musi być dodatni")


@dataclass(slots=True)
class StrategyConfig:
    """Parametry sterujące backtestem oraz uczeniem."""

    training_ratio: float = 0.65
    decision_threshold: float = 0.58
    capital: float = 5_000.0
    max_position: float = 0.75
    fee_rate: float = 0.0004
    evaluation_windows: Iterable[int] = (3, 6, 9)
    risk_limits: RiskLimits = field(default_factory=RiskLimits)

    def __post_init__(self) -> None:
        if not 0 < self.training_ratio < 1:
            raise ValueError("training_ratio musi leżeć w (0,1)")
        if not 0 < self.decision_threshold < 1:
            raise ValueError("decision_threshold musi leżeć w (0,1)")
        if self.capital <= 0:
            raise ValueError("capital musi być dodatni")
        if self.max_position <= 0:
            raise ValueError("max_position musi być dodatnie")
        if self.fee_rate < 0:
            raise ValueError("fee_rate nie może być ujemny")
        windows: List[int] = list(self.evaluation_windows)
        if not windows:
            raise ValueError("evaluation_windows nie może być puste")
        if any(win <= 0 for win in windows):
            raise ValueError("okna oceny muszą być dodatnie")
        self.evaluation_windows = tuple(sorted(set(windows)))
        self.risk_limits.validate()
