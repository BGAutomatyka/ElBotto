"""Kompleksowy interfejs wiersza poleceń dla programu ElBotto."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from importlib import metadata
from elbotto.application import ElBottoApplication
from elbotto.core.config import StrategyConfig
from elbotto.logging_utils import setup_logging
from elbotto.runtime.quickstart import DEFAULT_DATASET


CLI_COMMANDS: Dict[str, str] = {
    "backtest": "Uruchamia backtest i analizę wpływu wskaźników",
    "analyse": "Generuje raport z transakcji i rekomendacje korekt",
    "autotune": "Przeszukuje siatkę parametrów i zwraca najlepszą konfigurację",
    "gui": "Tworzy panel HTML z wynikami i sterowaniem",
    "simulate": "Generuje scenariusz bootstrapowy lub lead-lag",
    "package": "Buduje archiwum ZIP z gotową dystrybucją",
}

CONFIG_FIELDS: Tuple[str, ...] = (
    "training_ratio",
    "decision_threshold",
    "capital",
    "max_position",
    "fee_rate",
    "profit_spot_ratio",
    "min_reserve_ratio",
    "probe_ratio",
    "probe_confidence",
    "uncertainty_margin",
    "strong_signal_threshold",
    "strong_signal_multiplier",
)

RISK_FIELDS: Tuple[str, ...] = (
    "intraday_drawdown",
    "cvar_limit",
    "max_participation",
    "max_vpin",
    "slippage_budget_bps",
)


def run_cli(argv: Iterable[str] | None = None) -> int:
    """Punkt wejścia CLI. Zwraca kod wyjścia."""

    setup_logging()
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        arguments = ["backtest"]
    elif arguments[0] not in CLI_COMMANDS:
        arguments = ["backtest", *arguments]

    parser = _build_parser()
    args = parser.parse_args(arguments)
    command = args.command
    if command == "backtest":
        _cmd_backtest(args)
    elif command == "analyse":
        _cmd_analyse(args)
    elif command == "autotune":
        _cmd_autotune(args)
    elif command == "gui":
        _cmd_gui(args)
    elif command == "simulate":
        _cmd_simulate(args)
    elif command == "package":
        _cmd_package(args)
    else:  # pragma: no cover - zabezpieczenie przed regresją
        parser.print_help()
        return 1
    return 0


try:
    _CLI_VERSION = metadata.version("elbotto")
except metadata.PackageNotFoundError:  # pragma: no cover - środowisko developerskie
    _CLI_VERSION = "0.3.0"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="elbotto", description="Kompletny program ElBotto")
    parser.add_argument("--version", action="version", version=f"ElBotto {_CLI_VERSION}")
    subparsers = parser.add_subparsers(dest="command")

    _add_backtest_parser(subparsers)
    _add_analyse_parser(subparsers)
    _add_autotune_parser(subparsers)
    _add_gui_parser(subparsers)
    _add_simulate_parser(subparsers)
    _add_package_parser(subparsers)

    return parser


def _add_config_options(parser: argparse.ArgumentParser) -> None:
    for field in CONFIG_FIELDS:
        parser.add_argument(
            f"--{field.replace('_', '-')}",
            type=float,
            dest=field,
            help=f"Nadpisuje parametr {field}",
        )
    for field in RISK_FIELDS:
        parser.add_argument(
            f"--risk-{field.replace('_', '-')}",
            type=float,
            dest=f"risk_{field}",
            help=f"Nadpisuje limit ryzyka {field}",
        )


def _add_backtest_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("backtest", help=CLI_COMMANDS["backtest"])
    parser.add_argument("dataset", nargs="?", default=str(DEFAULT_DATASET), help="Ścieżka do pliku CSV z order book")
    parser.add_argument(
        "--json",
        dest="json_output",
        type=Path,
        help="Zapisz metryki do pliku JSON",
    )
    parser.add_argument(
        "--show-deps",
        action="store_true",
        help="Wyświetl także analizę zależności między parami",
    )
    _add_config_options(parser)


def _add_analyse_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("analyse", help=CLI_COMMANDS["analyse"])
    parser.add_argument("dataset", nargs="?", default=str(DEFAULT_DATASET))
    parser.add_argument(
        "--suggestions",
        action="store_true",
        help="Pokaż rozszerzone rekomendacje kalibracji",
    )
    _add_config_options(parser)


def _add_autotune_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("autotune", help=CLI_COMMANDS["autotune"])
    parser.add_argument("dataset", nargs="?", default=str(DEFAULT_DATASET))
    parser.add_argument("--grid-size", type=int, default=0, help="Rozszerz siatkę o dodatkową liczbę wariantów")
    parser.add_argument("--export", type=Path, help="Zapisz najlepszą konfigurację do JSON")
    _add_config_options(parser)


def _add_gui_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("gui", help=CLI_COMMANDS["gui"])
    parser.add_argument("dataset", nargs="?", default=str(DEFAULT_DATASET))
    parser.add_argument("--output", type=Path, default=Path("elbotto_dashboard.html"), help="Ścieżka pliku HTML")
    parser.add_argument("--auto", action="store_true", help="Przeprowadź auto-kalibrację przed renderem")
    parser.add_argument("--serve", action="store_true", help="Uruchom interaktywny serwer GUI")
    parser.add_argument("--host", default="127.0.0.1", help="Adres hosta serwera GUI")
    parser.add_argument("--port", type=int, default=8000, help="Port serwera GUI")
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("results"),
        help="Katalog na wyniki serwera (np. raporty, paczki)",
    )
    _add_config_options(parser)


def _add_simulate_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("simulate", help=CLI_COMMANDS["simulate"])
    parser.add_argument("dataset", nargs="?", default=str(DEFAULT_DATASET))
    parser.add_argument("--steps", type=int, default=12, help="Liczba kroków scenariusza bootstrapowego")
    parser.add_argument("--seed", type=int, default=17, help="Ziarno generatora losowego")
    _add_config_options(parser)


def _add_package_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    parser = subparsers.add_parser("package", help=CLI_COMMANDS["package"])
    parser.add_argument(
        "--output",
        type=str,
        default="elbotto_release.zip",
        help="Nazwa wynikowego archiwum",
    )


def _cmd_backtest(args: argparse.Namespace) -> None:
    app = _build_app(args)
    reports, impacts, dependencies = app.run_backtest(include_dependencies=args.show_deps)
    _print_reports(reports, impacts)
    if dependencies:
        for dep in dependencies:
            print(
                f"Korelacja {dep.symbol_a}/{dep.symbol_b}: {dep.correlation:.3f}, "
                f"lead-lag={dep.lead_lag:.2f}s"
            )
    if args.json_output:
        args.json_output.write_text(_serialize_reports(reports, impacts), encoding="utf-8")
        print(f"Zapisano metryki do {args.json_output}")


def _cmd_analyse(args: argparse.Namespace) -> None:
    app = _build_app(args)
    reports, impacts, _ = app.run_backtest()
    review = app.analyse_trades()
    print(f"Transakcji łącznie: {review.total_trades}, zysk netto: {review.total_pnl:.2f} USD")
    print(f"Oszczędności spot: {review.spot_saved:.2f} USD, kapitał handlowy: {review.trading_capital:.2f} USD")
    print(f"Niewykorzystane okazje: {review.counterfactual_opportunities}, uniknięte straty: {review.counterfactual_avoided}")
    print("Cechy odpowiadające za straty:")
    for effect in review.loss_drivers:
        print(f" - {effect.feature}: ΔPnL={effect.difference:.4f}")
    print("Cechy generujące zysk:")
    for effect in review.gain_drivers:
        print(f" + {effect.feature}: ΔPnL={effect.difference:.4f}")
    if args.suggestions and review.suggestions:
        print("Rekomendowane zmiany:")
        for suggestion in review.suggestions:
            print(f" * {suggestion.parameter} → {suggestion.suggested_value:.4f} ({suggestion.rationale})")


def _cmd_autotune(args: argparse.Namespace) -> None:
    app = _build_app(args)
    result = app.auto_tune(extra_grid=args.grid_size)
    best = result.best_config
    print("Najlepsza konfiguracja:")
    print(
        json.dumps(
            {
                "decision_threshold": best.decision_threshold,
                "max_position": best.max_position,
                "profit_spot_ratio": best.profit_spot_ratio,
                "strong_signal_multiplier": best.strong_signal_multiplier,
                "probe_ratio": best.probe_ratio,
                "training_ratio": best.training_ratio,
            },
            indent=2,
        )
    )
    print(f"Przetestowano kombinacji: {len(result.evaluations)}, score: {result.best_score:.2f}")
    if args.export:
        payload = {
            "decision_threshold": best.decision_threshold,
            "max_position": best.max_position,
            "profit_spot_ratio": best.profit_spot_ratio,
            "strong_signal_multiplier": best.strong_signal_multiplier,
            "probe_ratio": best.probe_ratio,
            "training_ratio": best.training_ratio,
        }
        args.export.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Zapisano konfigurację do {args.export}")


def _cmd_gui(args: argparse.Namespace) -> None:
    app = _build_app(args)
    if args.serve:
        app.serve_gui(host=args.host, port=args.port, block=True)
        return
    html = app.render_dashboard(auto=args.auto)
    args.output.write_text(html, encoding="utf-8")
    print(f"Panel zapisany do {args.output.resolve()}")


def _cmd_simulate(args: argparse.Namespace) -> None:
    app = _build_app(args)
    scenario = app.simulate(steps=args.steps, seed=args.seed)
    print(f"Wygenerowano {len(scenario)} kroków scenariusza. Pierwszy mid: {scenario[0].mid:.2f}")
    deps = app.dependencies()
    if deps:
        top = deps[0]
        print(
            f"Najsilniejsza zależność: {top.symbol_a}/{top.symbol_b} corr={top.correlation:.3f}, lead-lag={top.lead_lag:.2f}s"
        )


def _cmd_package(args: argparse.Namespace) -> None:
    app = ElBottoApplication()
    archive = app.package(args.output)
    print(f"Utworzono archiwum {archive}")


def _build_config_from_args(args: argparse.Namespace) -> StrategyConfig:
    config = StrategyConfig()
    overrides: Dict[str, Any] = {}
    for field in CONFIG_FIELDS:
        value = getattr(args, field, None)
        if value is not None:
            overrides[field] = value
    for field in RISK_FIELDS:
        value = getattr(args, f"risk_{field}", None)
        if value is not None:
            overrides[f"risk.{field}"] = value
    if overrides:
        config = config.clone_with(**overrides)
    return config


def _build_app(args: argparse.Namespace) -> ElBottoApplication:
    config = _build_config_from_args(args)
    dataset = Path(getattr(args, "dataset", str(DEFAULT_DATASET)))
    results_dir = getattr(args, "results_dir", Path("results"))
    if not isinstance(results_dir, Path):
        results_dir = Path(results_dir)
    return ElBottoApplication(config=config, dataset=dataset, results_dir=results_dir)


def _serialize_reports(reports, impacts) -> str:
    payload = {
        symbol: report.state.metrics for symbol, report in reports.items()
    }
    payload["loss_drivers"] = [effect.__dict__ for effect in impacts.loss_drivers(top_n=5)] if impacts else []
    payload["gain_drivers"] = [effect.__dict__ for effect in impacts.gain_drivers(top_n=5)] if impacts else []
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _print_reports(reports, impacts) -> None:
    for symbol, report in reports.items():
        metrics = report.state.metrics
        print(
            f"=== {symbol} ===\n"
            f"Transakcji: {metrics.get('trade_count', 0)}\n"
            f"Kapitał końcowy: {metrics.get('final_equity', 0.0):.2f} USD\n"
            f"Kapitał handlowy: {metrics.get('trading_capital', metrics.get('final_equity', 0.0)):.2f} USD\n"
            f"Oszczędności spot: {metrics.get('spot_saved', 0.0):.2f} USD\n"
            f"Zysk netto: {metrics.get('total_pnl', 0.0):.2f} USD, Max DD: {metrics.get('max_drawdown', 0.0):.2f} USD\n"
        )
    if impacts:
        print("Najważniejsze cechy wzmacniające wynik:")
        for effect in impacts.gain_drivers(top_n=3):
            print(f" + {effect.feature}: ΔPnL={effect.difference:.4f}")
        print("Cechy pogarszające wynik:")
        for effect in impacts.loss_drivers(top_n=3):
            print(f" - {effect.feature}: ΔPnL={effect.difference:.4f}")


__all__ = ["run_cli"]

