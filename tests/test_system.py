from pathlib import Path
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT / "src"), str(ROOT)])

from elbotto import (
    Backtester,
    DashboardApp,
    StrategyConfig,
    analyse_dependencies,
    bootstrap_scenarios,
    evaluate_feature_impacts,
    load_order_book_csv,
    run_quickstart,
)
from scripts.package_release import create_install_bundle

DATA_PATH = Path("data/binance_order_book_small.csv")


def test_backtester_and_reports():
    datasets = load_order_book_csv(DATA_PATH)
    reports = Backtester(StrategyConfig(training_ratio=0.6)).run(datasets)
    assert reports
    for symbol, report in reports.items():
        assert report.state.metrics["final_equity"] > 0
        assert report.interval_volatility
        assert report.validation_loss >= 0


def test_dependencies_and_bootstrap():
    datasets = load_order_book_csv(DATA_PATH)
    deps = analyse_dependencies(datasets)
    assert deps
    first = deps[0]
    assert first.symbol_a != first.symbol_b

    any_series = next(iter(datasets.values()))
    scenario = bootstrap_scenarios(any_series, steps=10, seed=7)
    assert len(scenario) == 10
    assert scenario[0].mid > 0


def test_dashboard_app():
    datasets = load_order_book_csv(DATA_PATH)
    reports = Backtester().run(datasets)
    app = DashboardApp(StrategyConfig(), reports)
    html = app.render()
    assert "ElBotto" in html
    updated = app.update_threshold(0.6)
    assert pytest.approx(updated) == 0.6
    trades = app.list_trades()
    assert isinstance(trades, list)


def test_feature_impact_report_and_quickstart():
    datasets = load_order_book_csv(DATA_PATH)
    reports, impacts = run_quickstart(DATA_PATH)
    assert reports
    assert impacts.aggregated
    loss = impacts.loss_drivers(top_n=2)
    gain = impacts.gain_drivers(top_n=2)
    assert isinstance(loss, list)
    assert isinstance(gain, list)
    effects = evaluate_feature_impacts(datasets, reports)
    assert effects.aggregated


def test_package_release():
    archive = create_install_bundle("test_bundle.zip")
    assert archive.exists()
    with zipfile.ZipFile(archive) as bundle:
        assert "pyproject.toml" in bundle.namelist()
    archive.unlink()
