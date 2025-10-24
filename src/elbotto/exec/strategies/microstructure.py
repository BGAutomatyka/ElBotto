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
    reinvest_allocation: float
    notional: float
    fee: float
    pnl_gross: float
    pnl: float
    confidence: float
    mode: str


@dataclass(slots=True)
class StrategyState:
    equity_curve: List[float]
    spot_balance: List[float]
    trading_balance: List[float]
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
        reserve_floor = self.config.capital * self.config.min_reserve_ratio
        equity_curve: List[float] = [capital]
        trading_curve: List[float] = [capital]
        spot_curve: List[float] = [spot]
        trades: List[Trade] = []
        total_pnl = 0.0
        total_fees = 0.0
        total_notional = 0.0
        max_notional = 0.0
        reinvested_total = 0.0
        probe_trades = 0
        strong_trades = 0
        skipped_due_to_reserve = 0
        skipped_uncertain = 0
        counterfactual_gain = 0.0
        counterfactual_loss = 0.0
        counterfactual_opportunities = 0
        counterfactual_avoided = 0
        emergency_transfers = 0.0
        good_decisions = 0
        bad_decisions = 0

        probs = self.model.predict_proba(self.features.features)
        for idx, prob in enumerate(probs):
            if self.features.target[idx] == 0.5:
                continue
            confidence = abs(prob - 0.5) * 2
            edge_bps = (prob - 0.5) * 10_000
            expected_slippage_bps = 3.0
            decision = decide_execution(
                edge_bps=edge_bps,
                fee_rate=self.config.fee_rate,
                expected_slippage_bps=expected_slippage_bps,
                confidence=confidence,
                threshold=self.config.decision_threshold,
            )
            price = self.features.features[idx][0]
            spread = self.features.spread[idx]
            direction = 1 if edge_bps >= 0 else -1
            net_edge = edge_bps - (self.config.fee_rate * 10_000) - expected_slippage_bps
            max_affordable = max(capital - reserve_floor, 0.0)
            max_affordable_size = max_affordable / price if price > 0 else 0.0

            size = 0.0
            mode = "skipped"
            execute = False

            if decision is not None:
                base_size = min(self.config.max_position, decision.size * self.config.max_position)
                size = min(base_size, max_affordable_size)
                mode = "standard"
                if confidence >= self.config.strong_signal_threshold:
                    strong_trades += 1
                    boosted = base_size * self.config.strong_signal_multiplier
                    size = min(boosted, self.config.max_position * self.config.strong_signal_multiplier, max_affordable_size)
                    mode = "strong"
                if size > 0:
                    execute = True
            else:
                threshold_lower = max(self.config.decision_threshold - self.config.uncertainty_margin, 0.0)
                if net_edge > 0 and confidence >= self.config.probe_confidence:
                    size = min(self.config.max_position * self.config.probe_ratio, max_affordable_size)
                    if size > 0:
                        execute = True
                        mode = "probe"
                        probe_trades += 1
                elif threshold_lower <= confidence < self.config.decision_threshold:
                    skipped_uncertain += 1

            if not execute or size <= 0:
                hypothetical_size = min(self.config.max_position, max_affordable_size)
                if hypothetical_size > 0:
                    hypothetical_fee = price * hypothetical_size * self.config.fee_rate
                    hypothetical_pnl = (
                        direction * (self.features.target[idx] - 0.5) * spread * hypothetical_size - hypothetical_fee
                    )
                    if hypothetical_pnl > 0:
                        counterfactual_gain += hypothetical_pnl
                        counterfactual_opportunities += 1
                    elif hypothetical_pnl < 0:
                        counterfactual_loss += abs(hypothetical_pnl)
                        counterfactual_avoided += 1
                else:
                    skipped_due_to_reserve += 1
                continue

            fee = price * size * self.config.fee_rate
            pnl_gross = direction * (self.features.target[idx] - 0.5) * spread * size
            pnl_net = pnl_gross - fee
            capital += pnl_net
            spot_allocation = max(0.0, pnl_net) * self.config.profit_spot_ratio
            reinvest_allocation = max(0.0, pnl_net) - spot_allocation
            if spot_allocation > 0:
                transfer = min(spot_allocation, capital)
                capital -= transfer
                spot += transfer
            reinvested_total += reinvest_allocation
            if capital < reserve_floor and spot > 0:
                needed = reserve_floor - capital
                rescue = min(spot, needed)
                if rescue > 0:
                    spot -= rescue
                    capital += rescue
                    emergency_transfers += rescue
            if capital < 0 and spot > 0:
                deficit = -capital
                rescue_extra = min(spot, deficit)
                if rescue_extra > 0:
                    spot -= rescue_extra
                    capital += rescue_extra
                    emergency_transfers += rescue_extra
            if capital < 0:
                capital = 0.0
            notional = price * size
            total_notional += notional
            total_pnl += pnl_net
            total_fees += fee
            max_notional = max(max_notional, notional)
            if pnl_net >= 0:
                good_decisions += 1
            else:
                bad_decisions += 1
            trades.append(
                Trade(
                    timestamp=self.features.timestamps[idx],
                    side="buy" if direction > 0 else "sell",
                    price=price,
                    size=size,
                    spot_allocation=spot_allocation,
                    reinvest_allocation=reinvest_allocation,
                    notional=notional,
                    fee=fee,
                    pnl_gross=pnl_gross,
                    pnl=pnl_net,
                    confidence=confidence,
                    mode=mode,
                )
            )
            total_equity = capital + spot
            equity_curve.append(total_equity)
            trading_curve.append(capital)
            spot_curve.append(spot)

        max_drawdown = 0.0
        peak = equity_curve[0] if equity_curve else 0.0
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = peak - value
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        avg_notional = total_notional / len(trades) if trades else 0.0
        final_total_equity = (equity_curve[-1] if equity_curve else capital + spot)
        metrics = {
            "trade_count": len(trades),
            "final_equity": final_total_equity,
            "trading_capital": capital,
            "spot_saved": spot,
            "reinvested_capital": reinvested_total,
            "total_pnl": total_pnl,
            "total_fees": total_fees,
            "average_trade_size_usd": avg_notional,
            "max_notional_usd": max_notional,
            "max_drawdown": max_drawdown,
            "decision_threshold": self.config.decision_threshold,
            "max_position": self.config.max_position,
            "training_ratio": self.config.training_ratio,
            "spot_ratio": spot / final_total_equity if final_total_equity else 0.0,
            "counterfactual_gain": counterfactual_gain,
            "counterfactual_loss": counterfactual_loss,
            "counterfactual_opportunities": counterfactual_opportunities,
            "counterfactual_avoided": counterfactual_avoided,
            "probe_trades": probe_trades,
            "strong_trades": strong_trades,
            "skipped_uncertain": skipped_uncertain,
            "skipped_due_to_reserve": skipped_due_to_reserve,
            "emergency_transfers": emergency_transfers,
            "good_decisions": good_decisions,
            "bad_decisions": bad_decisions,
            "spot_allocation_ratio": self.config.profit_spot_ratio,
            "reserve_floor": reserve_floor,
        }
        return StrategyState(
            equity_curve=equity_curve,
            spot_balance=spot_curve,
            trading_balance=trading_curve,
            metrics=metrics,
            trades=trades,
        )
