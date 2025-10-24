"""Rozszerzony panel HTML z kontrolą strategii i auto-tuningiem."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from elbotto.analysis.diagnostics import ImpactReport
from elbotto.analysis.trade_review import AdjustmentSuggestion, TradeReview, review_trades
from elbotto.backtest.engine import BacktestReport
from elbotto.core.config import StrategyConfig
from elbotto.data.orderbook import OrderBookSeries, load_order_book_csv
from elbotto.runtime.autotune import AutoTuneResult, auto_calibrate
from elbotto.runtime.quickstart import DEFAULT_DATASET, run_quickstart


@dataclass(slots=True)
class DashboardApp:
    """Zarządza stanem panelu oraz zapewnia interfejs do kalibracji."""

    config: StrategyConfig
    reports: Dict[str, BacktestReport]
    impacts: Optional[ImpactReport] = None
    review: Optional[TradeReview] = None
    dataset_path: Path = DEFAULT_DATASET
    auto_result: Optional[AutoTuneResult] = None
    _series_map: Dict[str, OrderBookSeries] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dataset(cls, config: StrategyConfig, dataset: Path | str = DEFAULT_DATASET) -> "DashboardApp":
        path = Path(dataset)
        series_map = load_order_book_csv(path)
        reports, impacts = run_quickstart(path, config, series_map=series_map)
        review = review_trades(reports, impacts)
        app = cls(
            config=config,
            reports=reports,
            impacts=impacts,
            review=review,
            dataset_path=path,
        )
        app._series_map = series_map
        return app

    def refresh(self, dataset: Path | str | None = None) -> None:
        """Ponownie przelicza raporty po zmianie danych lub konfiguracji."""

        if dataset is not None:
            self.dataset_path = Path(dataset)
            self._series_map = load_order_book_csv(self.dataset_path)
        if not self._series_map:
            self._series_map = load_order_book_csv(self.dataset_path)
        reports, impacts = run_quickstart(self.dataset_path, self.config, series_map=self._series_map)
        self.reports = reports
        self.impacts = impacts
        self.review = review_trades(reports, impacts)

    def manual_update(self, **parameters: float) -> StrategyConfig:
        """Ręczna kalibracja najważniejszych parametrów i natychmiastowe odświeżenie."""

        numeric_params: Dict[str, float] = {}
        for key, value in parameters.items():
            try:
                numeric_params[key] = float(value)
            except (TypeError, ValueError):
                continue
        self.config = self.config.clone_with(**numeric_params)
        self.refresh()
        return self.config

    def auto_optimize(self) -> StrategyConfig:
        """Uruchamia automatyczną regulację parametrów jedną komendą."""

        if not self._series_map:
            self._series_map = load_order_book_csv(self.dataset_path)
        result = auto_calibrate(self._series_map, self.config)
        self.config = result.best_config
        self.auto_result = result
        self.refresh()
        return self.config

    def trade_table(self) -> List[Dict[str, float | str]]:
        """Tabela transakcji z wartościami w dolarach."""

        rows: List[Dict[str, float | str]] = []
        for report in self.reports.values():
            for trade in report.state.trades:
                rows.append(
                    {
                        "symbol": report.symbol,
                        "timestamp": trade.timestamp,
                        "side": trade.side,
                        "price": trade.price,
                        "size": trade.size,
                        "notional_usd": trade.notional,
                        "pnl_usd": trade.pnl,
                        "spot_allocation_usd": trade.spot_allocation,
                        "fee_usd": trade.fee,
                    }
                )
        return rows

    def render(self) -> str:
        """Buduje stronę HTML z wszystkimi potrzebnymi sekcjami."""

        summary_rows = [self._render_symbol_row(symbol, report) for symbol, report in self.reports.items()]
        trades_rows = [self._render_trade_row(row) for row in self.trade_table()]
        loss_list = self._render_effects(self.review.loss_drivers if self.review else [], "Straty")
        gain_list = self._render_effects(self.review.gain_drivers if self.review else [], "Zysk")
        suggestions_html = self._render_suggestions(self.review.suggestions if self.review else [])
        manual_controls = self._render_controls()
        auto_summary = self._render_auto_summary()

        return (
            "<html><head><title>ElBotto</title><style>"
            "body{font-family:sans-serif;margin:1.5rem;} table{border-collapse:collapse;width:100%;margin-bottom:1.5rem;}"
            "th,td{border:1px solid #ccc;padding:0.35rem;text-align:center;}"
            "h1,h2{color:#0b3d2e;} .section{margin-bottom:2rem;} .loss{color:#b30000;} .gain{color:#06623b;}"
            "</style></head><body>"
            "<h1>Panel ElBotto – podsumowanie strategii</h1>"
            f"<div class='section'><h2>Wyniki na danych: {self.dataset_path.name}</h2>"
            "<table><thead><tr><th>Para</th><th>Transakcji</th><th>Kapitał końcowy (USD)</th>"
            "<th>Zysk netto (USD)</th><th>Średni rozmiar pozycji (USD)</th><th>Maks. pozycja (USD)</th><th>Maks. obsunięcie (USD)</th></tr></thead>"
            f"<tbody>{''.join(summary_rows)}</tbody></table></div>"
            f"<div class='section'><h2>Sterowanie ręczne</h2>{manual_controls}</div>"
            f"<div class='section'><h2>Autoregulacja</h2>{auto_summary}</div>"
            f"<div class='section'><h2>Analiza przyczyn</h2><div class='loss'>{loss_list}</div><div class='gain'>{gain_list}</div>{suggestions_html}</div>"
            "<div class='section'><h2>Historia transakcji</h2>"
            "<table><thead><tr><th>Para</th><th>Czas</th><th>Strona</th><th>Cena</th><th>Ilość</th>"
            "<th>Wartość (USD)</th><th>PNL (USD)</th><th>Alokacja spot (USD)</th><th>Prowizja (USD)</th></tr></thead>"
            f"<tbody>{''.join(trades_rows)}</tbody></table></div>"
            "</body></html>"
        )

    def _render_symbol_row(self, symbol: str, report: BacktestReport) -> str:
        metrics = report.state.metrics
        return (
            "<tr>"
            f"<td>{symbol}</td>"
            f"<td>{metrics.get('trade_count', 0)}</td>"
            f"<td>{metrics.get('final_equity', 0.0):.2f}</td>"
            f"<td>{metrics.get('total_pnl', 0.0):.2f}</td>"
            f"<td>{metrics.get('average_trade_size_usd', 0.0):.2f}</td>"
            f"<td>{metrics.get('max_notional_usd', 0.0):.2f}</td>"
            f"<td>{metrics.get('max_drawdown', 0.0):.2f}</td>"
            "</tr>"
        )

    def _render_trade_row(self, row: Dict[str, float | str]) -> str:
        return (
            "<tr>"
            f"<td>{row['symbol']}</td>"
            f"<td>{row['timestamp']}</td>"
            f"<td>{row['side']}</td>"
            f"<td>{row['price']:.2f}</td>"
            f"<td>{row['size']:.4f}</td>"
            f"<td>{row['notional_usd']:.2f}</td>"
            f"<td>{row['pnl_usd']:.4f}</td>"
            f"<td>{row['spot_allocation_usd']:.4f}</td>"
            f"<td>{row['fee_usd']:.4f}</td>"
            "</tr>"
        )

    def _render_controls(self) -> str:
        metrics = self._aggregate_metrics()
        return (
            "<p>Aktualny kapitał: <strong>{capital:.2f} USD</strong>, Zysk netto: <strong>{pnl:.2f} USD</strong>,"
            " Średnia pozycja: <strong>{avg_pos:.2f} USD</strong>.".format(
                capital=metrics["capital"],
                pnl=metrics["total_pnl"],
                avg_pos=metrics["avg_notional"],
            )
            + " Możesz zmienić parametry w locie, np. próg decyzyjny, maksymalny rozmiar pozycji czy limity ryzyka." \
            + " Dostępne klucze: decision_threshold, max_position, capital, fee_rate, training_ratio, risk.max_vpin." \
            + " W kodzie wywołaj <code>app.manual_update(decision_threshold=0.62, max_position=1.0)</code> aby zastosować zmiany."
        )

    def _render_auto_summary(self) -> str:
        if not self.auto_result:
            return (
                "<p>Przycisk <strong>Automat</strong> uruchamia siatkę mini-backtestów i wybiera najlepsze ustawienia."
                " Wywołaj <code>app.auto_optimize()</code>, aby dobrać parametry automatycznie.</p>"
            )
        best = self.auto_result.best_config
        rows = []
        for evaluation in self.auto_result.evaluations:
            rows.append(
                "<tr>"
                f"<td>{evaluation.decision_threshold:.3f}</td>"
                f"<td>{evaluation.max_position:.3f}</td>"
                f"<td>{evaluation.training_ratio:.3f}</td>"
                f"<td>{evaluation.total_pnl:.4f}</td>"
                f"<td>{evaluation.max_drawdown:.4f}</td>"
                "</tr>"
            )
        table = (
            "<table><thead><tr><th>Próg</th><th>Max pozycja</th><th>Training ratio</th><th>PNL</th><th>Max DD</th></tr></thead>"
            f"<tbody>{''.join(rows)}</tbody></table>"
        )
        return (
            f"<p>Automat wybrał konfigurację: próg={best.decision_threshold:.3f}, max_position={best.max_position:.2f}, "
            f"training_ratio={best.training_ratio:.2f}.<br/>Łączny wynik punktacji: {self.auto_result.best_score:.4f}</p>"
            + table
        )

    def _render_effects(self, effects: List[object], title: str) -> str:
        if not effects:
            return f"<p>Brak danych dla sekcji: {title}.</p>"
        items = []
        for effect in effects:
            feature = getattr(effect, "feature", None)
            if feature is not None:
                diff = getattr(effect, "difference", 0.0)
                items.append(f"<li>{feature}: ΔPnL={diff:.4f}</li>")
        css_class = "loss" if title == "Straty" else "gain"
        return f"<ul class='{css_class}'>{''.join(items)}</ul>"

    def _render_suggestions(self, suggestions: List[AdjustmentSuggestion]) -> str:
        if not suggestions:
            return "<p>Brak dodatkowych rekomendacji kalibracji – konfiguracja jest spójna.</p>"
        items = [
            f"<li><strong>{s.parameter}</strong>: {s.rationale} (sugerowana wartość: {s.suggested_value:.3f})</li>"
            for s in suggestions
        ]
        return "<div><h3>Rekomendowane poprawki</h3><ul>" + "".join(items) + "</ul></div>"

    def _aggregate_metrics(self) -> Dict[str, float]:
        capital = 0.0
        total_pnl = 0.0
        avg_notional = 0.0
        trade_count = 0
        for report in self.reports.values():
            metrics = report.state.metrics
            capital += metrics.get("final_equity", 0.0)
            total_pnl += metrics.get("total_pnl", 0.0)
            trade_count += metrics.get("trade_count", 0)
            avg_notional += metrics.get("average_trade_size_usd", 0.0) * metrics.get("trade_count", 0)
        avg_notional = avg_notional / trade_count if trade_count else 0.0
        return {"capital": capital, "total_pnl": total_pnl, "avg_notional": avg_notional}
