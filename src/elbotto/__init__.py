"""Publiczne API pakietu ElBotto."""

from importlib import metadata

from elbotto.analysis.diagnostics import ImpactReport, evaluate_feature_impacts
from elbotto.analysis.trade_review import AdjustmentSuggestion, TradeReview, review_trades
from elbotto.application import ElBottoApplication
from elbotto.backtest.engine import Backtester
from elbotto.bots.portfolio import BotSuite
from elbotto.core.config import StrategyConfig
from elbotto.crossasset.dependencies import analyse_dependencies
from elbotto.data.orderbook import load_order_book_csv
from elbotto.gui.app import DashboardApp
from elbotto.gui.server import run_gui_server
from elbotto.logging_utils import get_logger, setup_logging
from elbotto.runtime.autotune import AutoTuneResult, auto_calibrate
from elbotto.cli import run_cli
from elbotto.runtime.quickstart import run_quickstart
from elbotto.simulation.bootstrap import bootstrap_scenarios

try:
    __version__ = metadata.version("elbotto")
except metadata.PackageNotFoundError:  # pragma: no cover - rozwój lokalny
    __version__ = "0.4.0"

__all__ = [
    "Backtester",
    "BotSuite",
    "ImpactReport",
    "TradeReview",
    "AdjustmentSuggestion",
    "AutoTuneResult",
    "ElBottoApplication",
    "StrategyConfig",
    "setup_logging",
    "get_logger",
    "load_order_book_csv",
    "analyse_dependencies",
    "DashboardApp",
    "run_gui_server",
    "bootstrap_scenarios",
    "evaluate_feature_impacts",
    "review_trades",
    "run_quickstart",
    "auto_calibrate",
    "run_cli",
    "__version__",
]

