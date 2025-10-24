"""Centralna aplikacja integrująca wszystkie moduły ElBotto."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from elbotto.analysis.diagnostics import ImpactReport, evaluate_feature_impacts
from elbotto.analysis.trade_review import TradeReview, review_trades
from elbotto.backtest.engine import BacktestReport
from elbotto.core.config import StrategyConfig
from elbotto.crossasset.dependencies import DependencyResult, analyse_dependencies
from elbotto.data.orderbook import OrderBookSeries, load_order_book_csv
from elbotto.gui.app import DashboardApp
from elbotto.gui.server import run_gui_server
from elbotto.logging_utils import setup_logging
from elbotto.packaging import create_install_bundle
from elbotto.runtime.autotune import AutoTuneResult, auto_calibrate
from elbotto.runtime.quickstart import DEFAULT_DATASET, run_quickstart
from elbotto.simulation.bootstrap import ScenarioPoint, bootstrap_scenarios


@dataclass(slots=True)
class ElBottoApplication:
    """Profesjonalny punkt wejścia spinający CLI, GUI i analizy."""

    config: StrategyConfig = field(default_factory=StrategyConfig)
    dataset: Path = field(default_factory=lambda: DEFAULT_DATASET)
    results_dir: Path = field(default_factory=lambda: Path("results"))
    log_level: str = "INFO"
    logger: logging.Logger = field(init=False, repr=False)

    _series_map: Dict[str, OrderBookSeries] = field(default_factory=dict, init=False, repr=False)
    _dashboard: Optional[DashboardApp] = field(default=None, init=False, repr=False)
    _reports: Optional[Dict[str, BacktestReport]] = field(default=None, init=False, repr=False)
    _impacts: Optional[ImpactReport] = field(default=None, init=False, repr=False)
    _review: Optional[TradeReview] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        setup_logging(self.log_level)
        self.logger = logging.getLogger("elbotto.application")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.dataset = Path(self.dataset)
        self.logger.debug("Zainicjowano aplikację z dataset=%s", self.dataset)

    # ------------------------------------------------------------------
    # Operacje wysokiego poziomu
    # ------------------------------------------------------------------
    def run_backtest(
        self, *, include_dependencies: bool = False, refresh: bool = False
    ) -> Tuple[Dict[str, BacktestReport], ImpactReport, Optional[List[object]]]:
        """Przeprowadza backtest i (opcjonalnie) analizę zależności."""

        series = self._load_series(refresh=refresh)
        reports, impacts = run_quickstart(self.dataset, self.config, series_map=series)
        self._reports = reports
        self._impacts = impacts
        self._review = review_trades(reports, impacts)
        dependencies = analyse_dependencies(series) if include_dependencies else None
        self.logger.info(
            "Backtest ukończony: par=%d, metryk=%d",
            len(reports),
            len(impacts.aggregated) if impacts else 0,
        )
        return reports, impacts, dependencies

    def analyse_trades(self) -> TradeReview:
        """Zwraca raport z dotychczasowych transakcji."""

        if self._reports is None or self._impacts is None:
            self.run_backtest()
        if self._review is None:
            self._review = review_trades(self._reports or {}, self._impacts)
        return self._review

    def auto_tune(self, extra_grid: int = 0) -> AutoTuneResult:
        """Uruchamia automatyczną kalibrację parametrów."""

        series = self._load_series()
        grid_kwargs = self._build_grid(extra_grid) if extra_grid > 0 else {}
        result = auto_calibrate(series, self.config, **grid_kwargs)
        self.config = result.best_config
        self._invalidate_cached_outputs()
        self.logger.info(
            "Automat zakończony: threshold=%.3f, max_position=%.3f, wynik=%.4f",
            self.config.decision_threshold,
            self.config.max_position,
            result.best_score,
        )
        return result

    def render_dashboard(self, *, auto: bool = False, extra_grid: int = 0) -> str:
        """Buduje panel HTML – z opcjonalnym auto-tuningiem."""

        dashboard = self._ensure_dashboard()
        if auto:
            dashboard.auto_optimize(extra_grid=extra_grid)
            self.config = dashboard.config
        return dashboard.render()

    def serve_gui(self, host: str = "127.0.0.1", port: int = 8000, block: bool = True):
        """Uruchamia interaktywny serwer GUI."""

        return run_gui_server(
            host=host,
            port=port,
            config=self.config,
            dataset=self.dataset,
            results_dir=self.results_dir,
            block=block,
        )

    def simulate(self, *, steps: int = 12, seed: int = 17) -> List[ScenarioPoint]:
        """Generuje scenariusz bootstrapowy na podstawie bieżącego zbioru danych."""

        series = self._load_series()
        if not series:
            raise RuntimeError("Brak danych do symulacji – wczytaj dataset przed symulacją.")
        first = next(iter(series.values()))
        scenario = bootstrap_scenarios(first, steps=steps, seed=seed)
        self.logger.info("Wygenerowano scenariusz symulacyjny: steps=%d seed=%d", steps, seed)
        return scenario

    def dependencies(self) -> List[DependencyResult]:
        """Zwraca listę zależności między parami."""

        series = self._load_series()
        deps = analyse_dependencies(series)
        self.logger.info("Policzono %d zależności między parami", len(deps))
        return deps

    def package(self, filename: str = "elbotto_release.zip") -> Path:
        """Buduje archiwum instalacyjne projektu."""

        archive = create_install_bundle(filename)
        self.logger.info("Pakiet zapisany w: %s", archive)
        return archive

    # ------------------------------------------------------------------
    # Operacje pomocnicze
    # ------------------------------------------------------------------
    def update_config(self, **updates: float) -> StrategyConfig:
        """Aktualizuje konfigurację i czyści cache wyników."""

        self.config = self.config.clone_with(**updates)
        self._invalidate_cached_outputs()
        self.logger.debug("Zmieniono konfigurację: %s", updates)
        return self.config

    def reload_dataset(self, dataset: Path | str) -> None:
        """Zmienia źródło danych i czyści cache."""

        self.dataset = Path(dataset)
        self._series_map.clear()
        self._dashboard = None
        self._invalidate_cached_outputs()
        self.logger.info("Przełączono dataset na: %s", self.dataset)

    def evaluate_impacts(self) -> ImpactReport:
        """Zwraca szczegółowy raport wpływu cech."""

        if self._reports is None:
            self.run_backtest()
        series = self._load_series()
        impacts = evaluate_feature_impacts(series, self._reports or {})
        self._impacts = impacts
        return impacts

    # ------------------------------------------------------------------
    # Wewnętrzne narzędzia
    # ------------------------------------------------------------------
    def _load_series(self, *, refresh: bool = False) -> Dict[str, OrderBookSeries]:
        if refresh or not self._series_map:
            if not self.dataset.exists():
                raise FileNotFoundError(f"Nie znaleziono pliku z danymi: {self.dataset}")
            self._series_map = load_order_book_csv(self.dataset)
            self.logger.debug("Wczytano %d serii order book", len(self._series_map))
        return self._series_map

    def _ensure_dashboard(self) -> DashboardApp:
        if self._dashboard is None:
            self._dashboard = DashboardApp.from_dataset(self.config, self.dataset)
        else:
            self._dashboard.config = self.config
            self._dashboard.refresh(self.dataset)
        return self._dashboard

    def _invalidate_cached_outputs(self) -> None:
        self._reports = None
        self._impacts = None
        self._review = None
        if self._dashboard is not None:
            self._dashboard.config = self.config
            self._dashboard.refresh(self.dataset)

    def _build_grid(self, extra_grid: int) -> Dict[str, Iterable[float]]:
        steps = max(extra_grid, 1)

        def expand(base: float, rel_step: float, lower: float, upper: float) -> List[float]:
            values = {base}
            for i in range(1, steps + 1):
                up = base * (1 + rel_step * i)
                down = base * (1 - rel_step * i)
                values.add(min(max(up, lower), upper))
                values.add(min(max(down, lower), upper))
            return sorted(values)

        grid: Dict[str, Iterable[float]] = {}
        grid["thresholds"] = expand(self.config.decision_threshold, 0.04, 0.52, 0.95)
        grid["max_positions"] = expand(self.config.max_position, 0.15, 0.2, 2.5)
        grid["training_ratios"] = expand(self.config.training_ratio, 0.08, 0.5, 0.9)
        grid["spot_ratios"] = expand(self.config.profit_spot_ratio or 0.2, 0.1, 0.05, 0.95)
        grid["strong_multipliers"] = expand(self.config.strong_signal_multiplier, 0.1, 1.0, 3.0)
        grid["probe_ratios"] = expand(self.config.probe_ratio, 0.1, 0.02, 0.6)
        return grid
