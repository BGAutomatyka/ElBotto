"""Minimalistyczny panel HTML prezentujący metryki i rekomendacje."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from elbotto.backtest.engine import BacktestReport
from elbotto.core.config import StrategyConfig


@dataclass(slots=True)
class DashboardApp:
    config: StrategyConfig
    reports: Dict[str, BacktestReport]

    def render(self) -> str:
        rows: List[str] = []
        for symbol, report in self.reports.items():
            metrics = report.state.metrics
            rows.append(
                f"<tr><td>{symbol}</td><td>{metrics['trade_count']}</td><td>{metrics['final_equity']:.2f}</td>"
                f"<td>{report.validation_loss:.4f}</td></tr>"
            )
        body = "".join(rows)
        return (
            "<html><head><title>ElBotto</title></head><body>"
            "<h1>ElBotto – raport z prawdziwych danych</h1>"
            "<table><thead><tr><th>Para</th><th>Liczba transakcji</th><th>Kapitał końcowy</th><th>Walidacja</th></tr></thead>"
            f"<tbody>{body}</tbody></table>"
            "</body></html>"
        )

    def update_threshold(self, value: float) -> float:
        self.config.decision_threshold = float(value)
        return self.config.decision_threshold

    def list_trades(self) -> List[dict]:
        trades: List[dict] = []
        for report in self.reports.values():
            for trade in report.state.trades:
                trades.append({
                    "timestamp": trade.timestamp,
                    "side": trade.side,
                    "pnl": trade.pnl,
                })
        return trades
