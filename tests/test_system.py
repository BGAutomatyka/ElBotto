import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.extend([str(ROOT / "src"), str(ROOT)])

from elbotto import (
    Backtester,
    DashboardApp,
    StrategyConfig,
    analyse_dependencies,
    auto_calibrate,
    run_gui_server,
    bootstrap_scenarios,
    evaluate_feature_impacts,
    load_order_book_csv,
    review_trades,
    run_quickstart,
)
from elbotto.packaging import create_install_bundle

DATA_PATH = Path("data/binance_order_book_small.csv")


def test_backtester_and_reports():
    datasets = load_order_book_csv(DATA_PATH)
    reports = Backtester(StrategyConfig(training_ratio=0.6)).run(datasets)
    assert reports
    for symbol, report in reports.items():
        assert report.state.metrics["final_equity"] > 0
        assert "spot_saved" in report.state.metrics
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
    app = DashboardApp.from_dataset(StrategyConfig(), DATA_PATH)
    html = app.render()
    assert "ElBotto" in html
    trades = app.trade_table()
    assert isinstance(trades, list)
    if trades:
        assert "notional_usd" in trades[0]
        assert "reinvest_allocation_usd" in trades[0]
        assert "confidence" in trades[0]
    config = app.manual_update(decision_threshold=0.6, max_position=0.9)
    assert pytest.approx(config.decision_threshold) == 0.6
    config = app.manual_update(profit_spot_ratio=0.55, probe_ratio=0.2)
    assert pytest.approx(config.profit_spot_ratio) == 0.55
    auto_config = app.auto_optimize()
    assert 0.5 < auto_config.decision_threshold < 0.9
    assert 0.0 <= auto_config.profit_spot_ratio <= 0.95
    assert 0.02 <= auto_config.probe_ratio <= 0.5


def test_feature_impact_report_and_quickstart():
    datasets = load_order_book_csv(DATA_PATH)
    reports, impacts = run_quickstart(DATA_PATH, StrategyConfig())
    assert reports
    assert impacts.aggregated
    loss = impacts.loss_drivers(top_n=2)
    gain = impacts.gain_drivers(top_n=2)
    assert isinstance(loss, list)
    assert isinstance(gain, list)
    effects = evaluate_feature_impacts(datasets, reports)
    assert effects.aggregated
    review = review_trades(reports, impacts)
    assert review.total_trades >= 0
    assert review.spot_saved >= 0
    assert review.counterfactual_opportunities >= 0
    assert review.probe_trades >= 0
    autotune = auto_calibrate(datasets, StrategyConfig())
    assert autotune.best_config.decision_threshold > 0.5
    assert autotune.best_config.profit_spot_ratio > 0
    assert autotune.evaluations


def test_package_release():
    archive = create_install_bundle("test_bundle.zip")
    assert archive.exists()
    with zipfile.ZipFile(archive) as bundle:
        assert "pyproject.toml" in bundle.namelist()
    archive.unlink()


def test_cli_backtest_and_gui(tmp_path):
    env = os.environ.copy()
    existing_path = env.get("PYTHONPATH")
    env["PYTHONPATH"] = f"{ROOT / 'src'}" + (f":{existing_path}" if existing_path else "")
    cmd = [sys.executable, "-m", "elbotto", "backtest", str(DATA_PATH)]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    assert "Transakcji" in result.stdout
    html_path = tmp_path / "panel.html"
    cmd_gui = [
        sys.executable,
        "-m",
        "elbotto",
        "gui",
        str(DATA_PATH),
        "--output",
        str(html_path),
    ]
    subprocess.run(cmd_gui, check=True, env=env)
    assert html_path.exists()


def test_gui_server_actions(tmp_path):
    server, thread, runtime = run_gui_server(
        host="127.0.0.1",
        port=0,
        config=StrategyConfig(),
        dataset=DATA_PATH,
        results_dir=tmp_path,
        block=False,
    )
    try:
        host, port = server.server_address
        base_url = f"http://{host}:{port}"
        with urllib.request.urlopen(base_url) as response:
            content = response.read().decode("utf-8")
            assert "ElBotto" in content
        update_payload = urllib.parse.urlencode(
            {
                "dataset": str(DATA_PATH),
                "decision_threshold": "0.6",
            }
        ).encode("utf-8")
        urllib.request.urlopen(
            urllib.request.Request(f"{base_url}/update", data=update_payload, method="POST")
        )
        time.sleep(0.2)
        assert pytest.approx(runtime.app.config.decision_threshold) == 0.6
        autotune_payload = urllib.parse.urlencode({"command": "autotune", "grid_size": "1"}).encode("utf-8")
        urllib.request.urlopen(
            urllib.request.Request(f"{base_url}/action", data=autotune_payload, method="POST")
        )
        time.sleep(0.2)
        assert runtime.app.auto_result is not None
        simulate_payload = urllib.parse.urlencode({"command": "simulate", "steps": "5", "seed": "3"}).encode("utf-8")
        urllib.request.urlopen(
            urllib.request.Request(f"{base_url}/action", data=simulate_payload, method="POST")
        )
        time.sleep(0.2)
        assert runtime.last_simulation
    finally:
        server.shutdown()
        thread.join(timeout=5)
