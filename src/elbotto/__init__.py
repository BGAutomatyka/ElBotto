"""Publiczne API pakietu ElBotto."""

from elbotto.analysis.diagnostics import ImpactReport, evaluate_feature_impacts
from elbotto.analysis.trade_review import AdjustmentSuggestion, TradeReview, review_trades
from elbotto.backtest.engine import Backtester
from elbotto.bots.portfolio import BotSuite
from elbotto.core.config import StrategyConfig
from elbotto.data.orderbook import load_order_book_csv
from elbotto.crossasset.dependencies import analyse_dependencies
from elbotto.gui.app import DashboardApp
from elbotto.runtime.autotune import AutoTuneResult, auto_calibrate
from elbotto.runtime.quickstart import run_quickstart
from elbotto.simulation.bootstrap import bootstrap_scenarios

__all__ = [
    "Backtester",
    "BotSuite",
    "ImpactReport",
    "TradeReview",
    "AdjustmentSuggestion",
    "AutoTuneResult",
    "StrategyConfig",
    "load_order_book_csv",
    "analyse_dependencies",
    "DashboardApp",
    "bootstrap_scenarios",
    "evaluate_feature_impacts",
    "review_trades",
    "run_quickstart",
    "auto_calibrate",
]

