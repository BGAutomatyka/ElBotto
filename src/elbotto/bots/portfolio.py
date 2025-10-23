"""Moduł orkiestrujący boty w testach A/B."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from elbotto.backtest.engine import Backtester, BacktestReport
from elbotto.core.config import StrategyConfig
from elbotto.data.orderbook import OrderBookSeries


@dataclass(slots=True)
class BotSuite:
    """Zarządza kilkoma wariantami strategii."""

    config: StrategyConfig

    def run(self, series_map: Dict[str, OrderBookSeries]) -> Dict[str, BacktestReport]:
        backtester = Backtester(self.config)
        return backtester.run(series_map)
