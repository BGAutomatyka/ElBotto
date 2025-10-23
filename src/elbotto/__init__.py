"""Publiczne API pakietu ElBotto."""

from elbotto.analysis.diagnostics import ImpactReport, evaluate_feature_impacts
from elbotto.backtest.engine import Backtester
from elbotto.bots.portfolio import BotSuite
from elbotto.core.config import StrategyConfig
from elbotto.data.orderbook import load_order_book_csv
from elbotto.crossasset.dependencies import analyse_dependencies
from elbotto.gui.app import DashboardApp
from elbotto.runtime.quickstart import run_quickstart
from elbotto.simulation.bootstrap import bootstrap_scenarios

__all__ = [
    "Backtester",
    "BotSuite",
    "ImpactReport",
    "StrategyConfig",
    "load_order_book_csv",
    "analyse_dependencies",
    "DashboardApp",
    "bootstrap_scenarios",
    "evaluate_feature_impacts",
    "run_quickstart",
]

