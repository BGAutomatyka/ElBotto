"""Backtester operujący wyłącznie na rzeczywistych danych."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable


from elbotto.core.config import StrategyConfig
from elbotto.data.orderbook import OrderBookSeries
from elbotto.exec.strategies.microstructure import MicrostructureStrategy, StrategyState
from elbotto.microstructure.features import FeatureMatrix, build_feature_matrix, compute_event_windows
from elbotto.ml.models import LogisticModel


@dataclass(slots=True)
class BacktestReport:
    symbol: str
    state: StrategyState
    validation_loss: float
    interval_volatility: Dict[int, float]


class Backtester:
    """Trener strategii dla wielu par na danych historycznych."""

    def __init__(self, config: StrategyConfig | None = None, horizon: int = 5) -> None:
        self.config = config or StrategyConfig()
        self.horizon = horizon

    def _split(self, matrix: FeatureMatrix) -> tuple[FeatureMatrix, FeatureMatrix]:
        split_idx = int(len(matrix.features) * self.config.training_ratio)
        train = FeatureMatrix(
            features=matrix.features[:split_idx],
            target=matrix.target[:split_idx],
            spread=matrix.spread[:split_idx],
            timestamps=matrix.timestamps[:split_idx],
            feature_names=matrix.feature_names,
        )
        test = FeatureMatrix(
            features=matrix.features[split_idx:],
            target=matrix.target[split_idx:],
            spread=matrix.spread[split_idx:],
            timestamps=matrix.timestamps[split_idx:],
            feature_names=matrix.feature_names,
        )
        return train, test

    def run(self, series_map: Dict[str, OrderBookSeries]) -> Dict[str, BacktestReport]:
        reports: Dict[str, BacktestReport] = {}
        for symbol, series in series_map.items():
            features = build_feature_matrix(series, horizon=self.horizon)
            train_matrix, test_matrix = self._split(features)
            model = LogisticModel.train(
                train_matrix.features,
                train_matrix.target,
                train_matrix.spread,
                fee_rate=self.config.fee_rate,
            )
            validation_loss = model.score(
                test_matrix.features,
                test_matrix.target,
                test_matrix.spread,
                fee_rate=self.config.fee_rate,
            )
            strategy = MicrostructureStrategy(self.config, model, test_matrix)
            state = strategy.run()
            volatility = compute_event_windows(series, self.config.evaluation_windows)
            reports[symbol] = BacktestReport(
                symbol=symbol,
                state=state,
                validation_loss=validation_loss,
                interval_volatility=volatility,
            )
        return reports
