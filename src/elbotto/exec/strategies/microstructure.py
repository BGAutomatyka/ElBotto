"""Strategia mikrostrukturalna oparta na logistycznym modelu."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from elbotto.core.config import StrategyConfig
from elbotto.exec.execution_policy import decide_execution
from elbotto.ml.models import LogisticModel
from elbotto.microstructure.features import FeatureMatrix


@dataclass(slots=True)
class Trade:
    timestamp: str
    side: str
    price: float
    size: float
    spot_allocation: float
    notional: float
    fee: float
    pnl_gross: float
    pnl: float


@dataclass(slots=True)
class StrategyState:
    equity_curve: List[float]
    spot_balance: List[float]
    metrics: dict
    trades: List[Trade]


class MicrostructureStrategy:
    def __init__(self, config: StrategyConfig, model: LogisticModel, features: FeatureMatrix) -> None:
        self.config = config
        self.model = model
        self.features = features

    def run(self) -> StrategyState:
        capital = self.config.capital
        spot = 0.0
        equity_curve: List[float] = [capital]
        spot_curve: List[float] = [spot]
        trades: List[Trade] = []
        total_pnl = 0.0
        total_fees = 0.0
        total_notional = 0.0
        max_notional = 0.0

        probs = self.model.predict_proba(self.features.features)
        for idx, prob in enumerate(probs):
            if self.features.target[idx] == 0.5:
                continue
            edge_bps = (prob - 0.5) * 10_000
            decision = decide_execution(
                edge_bps=edge_bps,
                fee_rate=self.config.fee_rate,
                expected_slippage_bps=3.0,
                confidence=abs(prob - 0.5) * 2,
                threshold=self.config.decision_threshold,
            )
            if not decision:
                continue
            price = self.features.features[idx][0]
            size = min(self.config.max_position, decision.size)
            fee = price * size * self.config.fee_rate
            direction = 1 if decision.side == "buy" else -1
            pnl_gross = direction * (self.features.target[idx] - 0.5) * self.features.spread[idx] * size
            pnl_net = pnl_gross - fee
            capital += pnl_net
            spot_allocation = max(0.0, pnl_net) * 0.5
            spot += spot_allocation
            notional = price * size
            total_notional += notional
            total_pnl += pnl_net
            total_fees += fee
            max_notional = max(max_notional, notional)
            trades.append(
                Trade(
                    timestamp=self.features.timestamps[idx],
                    side=decision.side,
                    price=price,
                    size=size,
                    spot_allocation=spot_allocation,
                    notional=notional,
                    fee=fee,
                    pnl_gross=pnl_gross,
                    pnl=pnl_net,
                )
            )
            equity_curve.append(capital)
            spot_curve.append(spot)

        max_drawdown = 0.0
        peak = equity_curve[0]
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        avg_notional = total_notional / len(trades) if trades else 0.0
        metrics = {
            "trade_count": len(trades),
            "final_equity": capital,
            "spot_saved": spot,
            "total_pnl": total_pnl,
            "total_fees": total_fees,
            "average_trade_size_usd": avg_notional,
            "max_notional_usd": max_notional,
            "max_drawdown": max_drawdown,
            "decision_threshold": self.config.decision_threshold,
            "max_position": self.config.max_position,
            "training_ratio": self.config.training_ratio,
        }
        return StrategyState(equity_curve=equity_curve, spot_balance=spot_curve, metrics=metrics, trades=trades)
