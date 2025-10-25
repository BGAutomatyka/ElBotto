import os, csv, datetime, json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .storage import RESULTS_DIR, DEFAULTS, load_params, save_params, save_best, load_best, save_automation_state, load_automation_state, save_indicators, load_indicators
from .parsing import parse_incremental, parse_full, compute_equity
from .exporters import export_trades_csv, export_equity_csv
from .widgets.metrics import MetricsPanel
from .tabs.analysis import AnalysisTab
from .tabs.charts import ChartsTab
from .tabs.news_ai import NewsAITab
from .indicators import INDICATORS

# Optional: import other tabs if present
try:
    from elbotto_gui.tabs.backtest import BacktestTab
    from elbotto_gui.tabs.sweep import SweepTab
    from elbotto_gui.tabs.data_sweep import DataSweepTab
    from elbotto_gui.tabs.training import TrainingTab
    from elbotto_gui.tabs.live import LiveTab
    from elbotto_gui.tabs.trades import TradesTab
    from elbotto_gui.tabs.grid import GridTab
    from elbotto_gui.tabs.validator import ValidatorTab
    from elbotto_gui.tabs.autolab import AutoLabTab
    from elbotto_gui.tabs.regimes import RegimesTab
    HAVE_EXTRA_TABS = True
except Exception:
    HAVE_EXTRA_TABS = False

# Adaptive policy
from .ai.policy import suggest_params

class ControlCenter(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=8)
        self.master = master; self.pack(fill="both", expand=True)
        self.proc = None
        self.accum = {}; self.current_feats = []; self.trades=[]; self.equity_times=[]; self.equity_vals=[]
        self._build_ui(); self._load_params(); self._load_automation()

    def _build_ui(self):
        self.master.title("ElBotto – Control Center (ULTRA+ AI)")
        self.master.geometry("1400x900")

        # Automation switchboard
        auto = ttk.LabelFrame(self, text="Automation / Manual")
        auto.pack(fill="x")
        self.var_mode = tk.StringVar(value=DEFAULTS["automation_mode"])
        ttk.Radiobutton(auto, text="MANUAL", variable=self.var_mode, value="MANUAL").pack(side="left", padx=6)
        ttk.Radiobutton(auto, text="AUTO",    variable=self.var_mode, value="AUTO").pack(side="left", padx=6)
        self.var_auto_strategy = tk.BooleanVar(value=DEFAULTS["auto_strategy"])
        self.var_auto_risk     = tk.BooleanVar(value=DEFAULTS["auto_risk"])
        self.var_auto_news     = tk.BooleanVar(value=DEFAULTS["auto_news"])
        ttk.Checkbutton(auto, text="Strategy", variable=self.var_auto_strategy).pack(side="left", padx=8)
        ttk.Checkbutton(auto, text="Risk",     variable=self.var_auto_risk).pack(side="left", padx=8)
        ttk.Checkbutton(auto, text="News Influence", variable=self.var_auto_news).pack(side="left", padx=8)

        # Common params
        self.frm = ttk.LabelFrame(self, text="Common Parameters")
        self.frm.pack(fill="x")
        self.var_dataset = tk.StringVar(value=DEFAULTS["dataset"])
        self.var_symbols = tk.StringVar(value=DEFAULTS["symbols"])
        self.var_threshold = tk.DoubleVar(value=DEFAULTS["threshold"])
        self.var_capital = tk.DoubleVar(value=DEFAULTS["capital"])
        self.var_maxpos = tk.DoubleVar(value=DEFAULTS["max_position"])
        self.var_fee = tk.DoubleVar(value=DEFAULTS["fee"])
        self.var_windows = tk.StringVar(value=DEFAULTS["windows"])
        self.var_spread = tk.StringVar(value=DEFAULTS["spread_max"])
        self.var_tp = tk.StringVar(value=DEFAULTS["tp_bps"])
        self.var_sl = tk.StringVar(value=DEFAULTS["sl_bps"])
        self.var_risk = tk.StringVar(value=DEFAULTS["risk_per_trade"])
        self.var_extra = tk.StringVar(value=DEFAULTS.get("extra_args",""))

        r=0
        ttk.Label(self.frm, text="Dataset:").grid(row=r, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(self.frm, textvariable=self.var_dataset, width=70).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self.frm, text="Browse…", command=self._pick_dataset).grid(row=r, column=2, padx=6)
        r+=1
        ttk.Label(self.frm, text="Symbols:").grid(row=r, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(self.frm, textvariable=self.var_symbols, width=40).grid(row=r, column=1, sticky="w", padx=6)
        ttk.Label(self.frm, text="Windows:").grid(row=r, column=2, sticky="e")
        ttk.Entry(self.frm, textvariable=self.var_windows, width=18).grid(row=r, column=3, sticky="w", padx=6)
        r+=1
        ttk.Label(self.frm, text="Threshold:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(self.frm, textvariable=self.var_threshold, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(self.frm, text="Capital:").grid(row=r, column=2, sticky="e")
        ttk.Entry(self.frm, textvariable=self.var_capital, width=12).grid(row=r, column=3, sticky="w", padx=6)
        r+=1
        ttk.Label(self.frm, text="Max pos:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(self.frm, textvariable=self.var_maxpos, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(self.frm, text="Fee:").grid(row=r, column=2, sticky="e")
        ttk.Entry(self.frm, textvariable=self.var_fee, width=10).grid(row=r, column=3, sticky="w", padx=6)
        r+=1
        ttk.Label(self.frm, text="Spread max:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(self.frm, textvariable=self.var_spread, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(self.frm, text="TP/SL (bps):").grid(row=r, column=2, sticky="e")
        fr = ttk.Frame(self.frm); fr.grid(row=r, column=3, sticky="w")
        ttk.Entry(fr, textvariable=self.var_tp, width=7).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left", padx=4)
        ttk.Entry(fr, textvariable=self.var_sl, width=7).pack(side="left")
        r+=1
        ttk.Label(self.frm, text="Risk per trade:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(self.frm, textvariable=self.var_risk, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(self.frm, text="Extra args:").grid(row=r, column=2, sticky="e")
        ttk.Entry(self.frm, textvariable=self.var_extra, width=30).grid(row=r, column=3, sticky="w", padx=6)

        # Tabs
        self.nb = ttk.Notebook(self); self.nb.pack(fill="both", expand=True)
        self.var_analysis_script = tk.StringVar()
        self.tab_analysis = AnalysisTab(self.nb, self.var_analysis_script); self.nb.add(self.tab_analysis, text="Analysis")
        self.tab_news = NewsAITab(self.nb, RESULTS_DIR); self.nb.add(self.tab_news, text="News AI")
        self.tab_charts = ChartsTab(self.nb); self.nb.add(self.tab_charts, text="Charts")
        if HAVE_EXTRA_TABS:
            self.var_backtest_script = tk.StringVar(); self.nb.add(BacktestTab(self.nb, self.var_backtest_script), text="Backtest")
            self.nb.add(SweepTab(self.nb), text="Batch Sweep")
            self.nb.add(DataSweepTab(self.nb), text="Data Sweep")
            self.var_train_script = tk.StringVar(); self.nb.add(TrainingTab(self.nb, self.var_train_script), text="Training")
            self.var_paper_script = tk.StringVar(); self.var_live_script = tk.StringVar(); self.var_env = tk.StringVar(value="paper"); self.var_api_key=tk.StringVar(); self.var_api_secret=tk.StringVar()
            self.nb.add(LiveTab(self.nb, self.var_paper_script, self.var_live_script, self.var_env, self.var_api_key, self.var_api_secret), text="Paper/Live")
            self.nb.add(TradesTab(self.nb), text="Trades/Equity")
            self.nb.add(GridTab(self.nb), text="Param Grid")
            self.nb.add(ValidatorTab(self.nb), text="Validator")
            self.nb.add(AutoLabTab(self.nb), text="AutoLab")
            self.nb.add(RegimesTab(self.nb), text="Regimes")

        # Output
        split = ttk.PanedWindow(self, orient="vertical"); split.pack(fill="both", expand=True, pady=(6,0))
        self.metrics = MetricsPanel(split)
        logf = ttk.LabelFrame(split, text="Log")
        self.txt = tk.Text(logf, wrap="word"); self.txt.pack(fill="both", expand=True, padx=6, pady=6)
        split.add(self.metrics, weight=1); split.add(logf, weight=2)

        # Bottom
        bar = ttk.Frame(self); bar.pack(fill="x", pady=6)
        ttk.Button(bar, text="▶ Run", command=self._run_clicked).pack(side="left", padx=6)
        ttk.Button(bar, text="■ Stop", command=self._stop_clicked).pack(side="left", padx=6)
        ttk.Button(bar, text="Save config", command=self._save_params).pack(side="left", padx=6)
        self.status = ttk.Label(bar, text="Ready"); self.status.pack(side="right", padx=6)

        self.after(200, self._tick)

    def _pick_dataset(self):
        p = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV","*.csv"),("All","*.*")])
        if p: self.var_dataset.set(p)

    def _load_params(self):
        cfg = load_params()
        self.var_dataset.set(cfg.get("dataset")); self.var_symbols.set(cfg.get("symbols"))
        self.var_threshold.set(cfg.get("threshold",0.5)); self.var_capital.set(cfg.get("capital",5000.0))
        self.var_maxpos.set(cfg.get("max_position",1.0)); self.var_fee.set(cfg.get("fee",0.0002))
        self.var_windows.set(cfg.get("windows","3 6 9")); self.var_spread.set(cfg.get("spread_max",""))
        self.var_tp.set(cfg.get("tp_bps","")); self.var_sl.set(cfg.get("sl_bps","")); self.var_risk.set(cfg.get("risk_per_trade",""))
        self.var_extra.set(cfg.get("extra_args",""))

    def _load_automation(self):
        st = load_automation_state()
        self.var_mode.set(st.get("mode","MANUAL"))
        self.var_auto_strategy.set(st.get("auto_strategy",True))
        self.var_auto_risk.set(st.get("auto_risk",True))
        self.var_auto_news.set(st.get("auto_news",True))

    def _save_params(self):
        cfg = {
            "dataset": self.var_dataset.get(), "symbols": self.var_symbols.get(),
            "threshold": float(self.var_threshold.get()), "capital": float(self.var_capital.get()),
            "max_position": float(self.var_maxpos.get()), "fee": float(self.var_fee.get()),
            "windows": self.var_windows.get(), "spread_max": self.var_spread.get(),
            "tp_bps": self.var_tp.get(), "sl_bps": self.var_sl.get(), "risk_per_trade": self.var_risk.get(),
            "extra_args": self.var_extra.get(), "append_indicators_flag": False, "required_columns": "timestamp,price,volume",
            "automation_mode": self.var_mode.get(), "auto_strategy": self.var_auto_strategy.get(),
            "auto_risk": self.var_auto_risk.get(), "auto_news": self.var_auto_news.get()
        }
        save_params(cfg); save_automation_state({"mode": self.var_mode.get(), "auto_strategy": self.var_auto_strategy.get(), "auto_risk": self.var_auto_risk.get(), "auto_news": self.var_auto_news.get()})
        messagebox.showinfo("Saved","Configuration saved.")

    # Running processes (simplified: we adjust args before run; for live mid-run adaptation, integrate via your bot reading results/best_config.json)
    def _build_args(self, script):
        args = [Path(".venv")/"Scripts"/"python.exe", script or "run_quickstart_tuned.py",
                "--dataset", self.var_dataset.get(),
                "--threshold", str(self.var_threshold.get()),
                "--capital", str(self.var_capital.get()),
                "--max-position", str(self.var_maxpos.get()),
                "--fee", str(self.var_fee.get()),
                "--windows", *self.var_windows.get().split()]
        if self.var_symbols.get().strip(): args += ["--symbols", *self.var_symbols.get().split()]
        if self.var_spread.get(): args += ["--spread-max", str(self.var_spread.get())]
        if self.var_tp.get(): args += ["--take-profit-bps", str(self.var_tp.get())]
        if self.var_sl.get(): args += ["--stop-loss-bps", str(self.var_sl.get())]
        if self.var_risk.get(): args += ["--risk-per-trade", str(self.var_risk.get())]
        if self.var_extra.get().strip(): args += self.var_extra.get().split()
        return args

    def _apply_automation(self):
        if self.var_mode.get() != "AUTO": return
        # Pull symbol sentiments
        sent_btc = self.tab_news.get_symbol_sentiment("BTCUSDT") if self.var_auto_news.get() else 0.0
        # TODO: regime metrics hook — here use a placeholder volatility=1.0, regime='calm'
        regime = "calm"; vol = 1.0
        base = {
            "threshold": float(self.var_threshold.get()),
            "risk_per_trade": self.var_risk.get(),
            "max_position": float(self.var_maxpos.get())
        }
        flags = {"auto_strategy": self.var_auto_strategy.get(), "auto_risk": self.var_auto_risk.get()}
        newp = suggest_params(base, regime, vol, sent_btc, flags)
        # Apply into GUI fields (previewable)
        self.var_threshold.set(newp.get("threshold", self.var_threshold.get()))
        self.var_risk.set(str(newp.get("risk_per_trade", self.var_risk.get())))
        self.var_maxpos.set(newp.get("max_position", self.var_maxpos.get()))

    def _run_clicked(self):
        self._apply_automation()  # adjust params just-in-time
        script = self.var_analysis_script.get() if hasattr(self, "var_analysis_script") else "run_quickstart_tuned.py"
        args = self._build_args(script)
        self._append(f"[RUN] {' '.join(map(str,args))}\n")
        # Minimal runner inline
        import subprocess, threading
        self.txt.delete("1.0","end"); self.accum = {}; self.current_feats=[]; self.trades=[]
        self.status.config(text="Running…")
        def worker():
            try:
                proc = subprocess.Popen([str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
                for line in proc.stdout:
                    self._on_line(line)
                rc = proc.wait(); self._on_line(f"[EXIT] {rc}\n")
            except FileNotFoundError:
                self._on_line("[ERROR] .venv\\Scripts\\python.exe not found.\n")
            except Exception as e:
                self._on_line(f"[ERROR] {e!r}\n")
        threading.Thread(target=worker, daemon=True).start()

    def _stop_clicked(self):
        messagebox.showinfo("Stop", "Stop wymaga pełnego runnera; użyj wersji ULTRA jeśli chcesz kill/stop.")

    def _append(self, s): self.txt.insert("end", s); self.txt.see("end")

    def _on_line(self, line):
        self._append(line)
        parse_incremental(line, self.accum); self.metrics.update_metrics(self.accum)
        feats = self.accum.get("features", [])
        if feats: self.current_feats = feats; self.metrics.set_features(feats)
        if "trades" in self.accum: self.trades = self.accum["trades"]
        if line.startswith("[EXIT]"):
            try:
                # finalize
                if self.trades:
                    times, eq = compute_equity(self.trades, starting_capital=float(self.var_capital.get()))
                    export_trades_csv(self.trades, RESULTS_DIR/"trades_latest.csv")
                    export_equity_csv(times, eq, RESULTS_DIR/"equity_latest.csv")
                    self._append("[INFO] Exported trades/equity.\n")
                if self.current_feats:
                    (RESULTS_DIR/"metrics_latest_features.csv").write_text("feature,delta,sign\n" + "\n".join(f"{n},{v},{s}" for n,v,s in self.current_feats), encoding="utf-8")
            except Exception as e:
                self._append(f"[WARN] finalize failed: {e!r}\n")
            self.status.config(text="Finished")

    def _tick(self):
        # periodic automation (e.g., preview tweaks every few seconds in AUTO)
        if self.var_mode.get()=="AUTO":
            try:
                self._apply_automation()
            except Exception:
                pass
        self.after(1000, self._tick)

def main():
    root = tk.Tk(); ControlCenter(root); root.mainloop()

if __name__ == "__main__": main()
