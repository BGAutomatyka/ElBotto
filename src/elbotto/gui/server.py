"""Lekki serwer HTTP udostępniający pełne GUI programu ElBotto."""

from __future__ import annotations

import html
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs

from elbotto.core.config import StrategyConfig
from elbotto.gui.app import DashboardApp
from elbotto.runtime.quickstart import DEFAULT_DATASET
from elbotto.runtime.autotune import AutoTuneResult
from elbotto.simulation.bootstrap import ScenarioPoint, bootstrap_scenarios
from elbotto.packaging import create_install_bundle

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


class GuiRuntime:
    """Przechowuje stan panelu i obsługuje wszystkie akcje."""

    def __init__(
        self,
        config: StrategyConfig | None = None,
        dataset: Path | str = DEFAULT_DATASET,
        results_dir: Path | str = Path("results"),
    ) -> None:
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.dataset_path = Path(dataset)
        self.app = DashboardApp.from_dataset(config or StrategyConfig(), self.dataset_path)
        self.config = self.app.config
        self.status_messages: List[str] = ["Serwer uruchomiony – gotowy do pracy."]
        self.last_simulation: List[ScenarioPoint] = []
        self.last_package: Optional[Path] = None
        self._lock = threading.Lock()

    # ------------------------ public API ---------------------------------
    def build_page(self) -> str:
        """Zwraca kompletną stronę HTML z formularzami i wynikami."""

        with self._lock:
            panel_fragment = _extract_body(self.app.render())
            config = self.app.config
            dataset = str(self.dataset_path)
            status_html = self._render_status()
            simulation_html = self._render_simulation()
            package_html = self._render_package()
            config_form = self._render_config_form(config, dataset)
            actions = self._render_actions()

        html_page = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'/><title>ElBotto GUI</title>"
            "<style>body{font-family:sans-serif;margin:1.5rem;}h1{color:#0b3d2e;}"
            ".grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0.5rem;}"
            "label{display:flex;flex-direction:column;font-size:0.9rem;color:#0b3d2e;}"
            "input,button{padding:0.45rem;font-size:0.95rem;}button{cursor:pointer;background:#0b3d2e;color:#fff;border:none;border-radius:4px;}"
            "button.secondary{background:#1b6ca8;}button.danger{background:#a83232;}"
            "section{margin-bottom:2rem;padding:1rem;border:1px solid #d7d7d7;border-radius:6px;background:#fafafa;}"
            "table{border-collapse:collapse;width:100%;margin-top:1rem;}th,td{border:1px solid #ccc;padding:0.35rem;text-align:center;}"
            "ul{margin:0;padding-left:1.2rem;} .log{max-height:160px;overflow-y:auto;background:#fff;border:1px solid #ddd;padding:0.5rem;}"
            ".forms{display:grid;grid-template-columns:1fr;gap:1rem;} .actions{display:flex;flex-wrap:wrap;gap:0.5rem;}"
            "</style></head><body><h1>ElBotto – panel sterujący</h1>"
            f"<section><h2>Konfiguracja i dane</h2>{config_form}</section>"
            f"<section><h2>Akcje</h2>{actions}</section>"
            f"<section><h2>Log zdarzeń</h2>{status_html}{simulation_html}{package_html}</section>"
            f"<section><h2>Raport strategii</h2>{panel_fragment}</section>"
            "</body></html>"
        )
        return html_page

    def update_config(self, data: Dict[str, List[str]]) -> None:
        """Aktualizuje konfigurację i opcjonalnie przeładowuje dane."""

        with self._lock:
            dataset = data.get("dataset", [""])[0].strip()
            if dataset:
                new_path = Path(dataset)
                if new_path.exists():
                    self.dataset_path = new_path
                    self.status_messages.append(f"Przeładowano dane z pliku: {new_path}")
                    self.app.refresh(self.dataset_path)
                else:
                    self.status_messages.append(f"⚠️ Plik {new_path} nie istnieje – pozostaję przy poprzednim.")
            updates: Dict[str, float] = {}
            for field in CONFIG_FIELDS:
                value = data.get(field, [""])[0].strip()
                if value:
                    try:
                        updates[field] = float(value)
                    except ValueError:
                        self.status_messages.append(f"⚠️ Nieprawidłowa wartość dla {field}: {value}")
            for field in RISK_FIELDS:
                name = f"risk.{field}"
                value = data.get(name, [""])[0].strip()
                if value:
                    try:
                        updates[name] = float(value)
                    except ValueError:
                        self.status_messages.append(f"⚠️ Nieprawidłowa wartość dla {name}: {value}")
            if updates:
                try:
                    self.app.manual_update(**updates)
                    self.config = self.app.config
                    self.status_messages.append(
                        "Zastosowano nową konfigurację: "
                        + ", ".join(f"{k}={v}" for k, v in updates.items())
                    )
                except ValueError as exc:
                    self.status_messages.append(f"⚠️ Błąd konfiguracji: {exc}")
            self._trim_status()

    def run_command(self, data: Dict[str, List[str]]) -> None:
        """Uruchamia jedną z komend odpowiadających dawnym poleceniom CLI."""

        command = data.get("command", ["backtest"])[0]
        with self._lock:
            try:
                if command == "backtest":
                    self.app.refresh()
                    metrics = self.app._aggregate_metrics()
                    self.status_messages.append(
                        "Backtest zakończony: transakcji={trade_count}, zysk={pnl:.2f} USD, spot={spot:.2f} USD".format(
                            trade_count=int(metrics.get("trade_count", 0)),
                            pnl=metrics.get("total_pnl", 0.0),
                            spot=metrics.get("spot", 0.0),
                        )
                    )
                elif command == "analyse":
                    self.app.refresh()
                    review = self.app.review
                    if review:
                        top_loss = review.loss_drivers[0].feature if review.loss_drivers else "brak"
                        top_gain = review.gain_drivers[0].feature if review.gain_drivers else "brak"
                        self.status_messages.append(
                            "Analiza decyzji: zysk netto={pnl:.2f} USD, najlepszy czynnik={gain}, najgorszy={loss}".format(
                                pnl=review.total_pnl,
                                gain=top_gain,
                                loss=top_loss,
                            )
                        )
                    else:
                        self.status_messages.append("Brak danych do analizy.")
                elif command == "autotune":
                    grid_size = max(_safe_int(data.get("grid_size", ["0"])[0]), 0)
                    result = self.app.auto_optimize(extra_grid=grid_size)
                    best: StrategyConfig = result
                    auto_result: AutoTuneResult | None = self.app.auto_result
                    score = auto_result.best_score if auto_result else 0.0
                    self.status_messages.append(
                        "Automat zakończony: threshold={thr:.3f}, max_pos={maxp:.3f}, wynik={score:.4f}".format(
                            thr=best.decision_threshold,
                            maxp=best.max_position,
                            score=score,
                        )
                    )
                    if grid_size:
                        self.status_messages.append(f"Rozszerzona siatka o {grid_size} krok(i) na stronę.")
                elif command == "simulate":
                    steps = max(_safe_int(data.get("steps", ["12"])[0]), 1)
                    seed = _safe_int(data.get("seed", ["17"])[0])
                    if not self.app._series_map:
                        self.app.refresh()
                    series = next(iter(self.app._series_map.values()))
                    self.last_simulation = bootstrap_scenarios(series, steps=steps, seed=seed)
                    self.status_messages.append(
                        f"Wygenerowano scenariusz symulacyjny (steps={steps}, seed={seed})."
                    )
                elif command == "package":
                    filename = data.get("output", ["elbotto_gui_bundle.zip"])[0] or "elbotto_gui_bundle.zip"
                    archive = create_install_bundle(filename)
                    self.last_package = archive
                    self.status_messages.append(f"Pakiet instalacyjny zapisany w: {archive}")
                else:
                    self.status_messages.append(f"⚠️ Nieznana komenda: {command}")
            except Exception as exc:  # pragma: no cover - zabezpieczenie serwera
                self.status_messages.append(f"⚠️ Błąd podczas wykonania {command}: {exc}")
            self._trim_status()

    # ------------------------ rendering pomocnicze ------------------------
    def _render_config_form(self, config: StrategyConfig, dataset: str) -> str:
        config_inputs = []
        for field in CONFIG_FIELDS:
            value = getattr(config, field)
            config_inputs.append(
                "<label>{name}<input type='number' name='{name}' step='any' value='{value}'/></label>".format(
                    name=field,
                    value=html.escape(f"{value:.6f}" if isinstance(value, float) else str(value)),
                )
            )
        risk_inputs = []
        for field in RISK_FIELDS:
            value = getattr(config.risk_limits, field)
            risk_inputs.append(
                "<label>risk.{name}<input type='number' name='risk.{name}' step='any' value='{value}'/></label>".format(
                    name=field,
                    value=html.escape(f"{value:.6f}" if isinstance(value, float) else str(value)),
                )
            )
        return (
            "<form method='post' action='/update' class='forms'>"
            f"<label>Dane (CSV)<input type='text' name='dataset' value='{html.escape(dataset)}'/></label>"
            f"<div class='grid'>{''.join(config_inputs)}</div>"
            f"<div class='grid'>{''.join(risk_inputs)}</div>"
            "<button type='submit'>Zastosuj zmiany</button>"
            "</form>"
        )

    def _render_actions(self) -> str:
        return (
            "<div class='actions'>"
            "<form method='post' action='/action'>"
            "<input type='hidden' name='command' value='backtest'/>"
            "<button type='submit'>Backtest</button>"
            "</form>"
            "<form method='post' action='/action'>"
            "<input type='hidden' name='command' value='analyse'/>"
            "<button type='submit'>Analiza decyzji</button>"
            "</form>"
            "<form method='post' action='/action'>"
            "<input type='hidden' name='command' value='autotune'/>"
            "<label>Siatka<input type='number' name='grid_size' value='0' step='1'/></label>"
            "<button type='submit'>Automat</button>"
            "</form>"
            "<form method='post' action='/action'>"
            "<input type='hidden' name='command' value='simulate'/>"
            "<label>Kroki<input type='number' name='steps' value='12' step='1' min='1'/></label>"
            "<label>Ziarno<input type='number' name='seed' value='17' step='1'/></label>"
            "<button type='submit'>Symulacja</button>"
            "</form>"
            "<form method='post' action='/action'>"
            "<input type='hidden' name='command' value='package'/>"
            "<label>Archiwum<input type='text' name='output' value='elbotto_gui_bundle.zip'/></label>"
            "<button type='submit'>Pakiet</button>"
            "</form>"
            "</div>"
        )

    def _render_status(self) -> str:
        if not self.status_messages:
            return "<p>Brak zdarzeń.</p>"
        items = "".join(f"<li>{html.escape(message)}</li>" for message in reversed(self.status_messages[-10:]))
        return f"<div class='log'><ul>{items}</ul></div>"

    def _render_simulation(self) -> str:
        if not self.last_simulation:
            return ""
        rows = []
        preview = self.last_simulation[:10]
        for idx, point in enumerate(preview, start=1):
            rows.append(
                "<tr><td>{idx}</td><td>{mid:.4f}</td><td>{spread:.6f}</td><td>{micro:.4f}</td></tr>".format(
                    idx=idx, mid=point.mid, spread=point.spread, micro=point.microprice
                )
            )
        table = (
            "<h3>Ostatnia symulacja</h3>"
            "<table><thead><tr><th>#</th><th>Mid</th><th>Spread</th><th>Microprice</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
        return table

    def _render_package(self) -> str:
        if not self.last_package:
            return ""
        path = html.escape(str(self.last_package))
        return f"<p><strong>Pakiet:</strong> {path}</p>"

    def _trim_status(self) -> None:
        if len(self.status_messages) > 50:
            del self.status_messages[:-50]


class _GuiRequestHandler(BaseHTTPRequestHandler):
    runtime: GuiRuntime

    def do_GET(self) -> None:  # noqa: N802
        content = self.runtime.build_page().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        data = parse_qs(body)
        if self.path == "/update":
            self.runtime.update_config(data)
        elif self.path == "/action":
            self.runtime.run_command(data)
        else:
            self.send_error(404, "Nieobsługiwany endpoint")
            return
        self.send_response(303)
        self.send_header("Location", "/")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: D401
        """Wyłącza logowanie na STDOUT."""


class GuiHTTPServer(ThreadingHTTPServer):
    """Prosty serwer HTTP z obsługą wielowątkową."""


def run_gui_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    config: StrategyConfig | None = None,
    dataset: Path | str = DEFAULT_DATASET,
    results_dir: Path | str = Path("results"),
    block: bool = True,
):
    """Uruchamia serwer GUI i opcjonalnie blokuje wątku główny."""

    runtime = GuiRuntime(config=config, dataset=dataset, results_dir=results_dir)
    handler = _GuiRequestHandler
    handler.runtime = runtime
    server = GuiHTTPServer((host, port), handler)

    if block:
        try:
            print(f"Serwer GUI działa pod adresem http://{server.server_address[0]}:{server.server_address[1]}")
            server.serve_forever()
        except KeyboardInterrupt:  # pragma: no cover - interakcja użytkownika
            print("Zatrzymywanie serwera GUI...")
        finally:
            server.server_close()
            return server
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread, runtime


def _extract_body(html_doc: str) -> str:
    start = html_doc.find("<body>")
    end = html_doc.rfind("</body>")
    if start != -1 and end != -1:
        return html_doc[start + len("<body>") : end]
    return html_doc


def _safe_int(value: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

