"""Polityka wykonania zleceń z budżetem poślizgu."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ExecutionDecision:
    side: str
    aggressive: bool
    size: float
    reason: str


def decide_execution(edge_bps: float, fee_rate: float, expected_slippage_bps: float, confidence: float, threshold: float) -> ExecutionDecision | None:
    """Zwraca decyzję o wejściu na rynek lub brak transakcji."""

    if confidence < threshold:
        return None
    net_edge = edge_bps - (fee_rate * 10_000) - expected_slippage_bps
    if net_edge <= 0:
        return None
    aggressive = net_edge > 5
    side = "buy" if edge_bps > 0 else "sell"
    size = min(1.0, confidence)
    return ExecutionDecision(side=side, aggressive=aggressive, size=size, reason=f"edge={edge_bps:.2f}bps")
