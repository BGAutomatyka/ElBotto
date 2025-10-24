from pathlib import Path

from elbotto.application import ElBottoApplication
from elbotto.core.config import StrategyConfig

DATA_PATH = Path("data/binance_order_book_small.csv")


def test_application_workflow(tmp_path):
    app = ElBottoApplication(StrategyConfig(), dataset=DATA_PATH, results_dir=tmp_path)
    reports, impacts, deps = app.run_backtest(include_dependencies=True)
    assert reports
    assert impacts.aggregated
    assert deps is not None
    review = app.analyse_trades()
    assert review.total_trades >= 0
    html = app.render_dashboard()
    assert "ElBotto" in html
    scenario = app.simulate(steps=4, seed=3)
    assert len(scenario) == 4
    auto = app.auto_tune(extra_grid=1)
    assert auto.best_config.decision_threshold > 0
    deps_again = app.dependencies()
    assert deps_again
    bundle = app.package("test_bundle_cli.zip")
    assert bundle.exists()
    bundle.unlink()
