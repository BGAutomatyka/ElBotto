
import os, csv, datetime, json
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .presets import PRESETS
from .storage import RESULTS_DIR, DEFAULTS, load_params, save_params, load_profiles, save_profiles, load_indicators, save_indicators
from .runner import ProcessRunner
from .parsing import parse_incremental, parse_full
from .indicators import INDICATORS
from .widgets.metrics import MetricsPanel
from .widgets.indicator_window import IndicatorWindow
from .tabs.analysis import AnalysisTab
from .tabs.backtest import BacktestTab
from .tabs.sweep import SweepTab
from .tabs.data_sweep import DataSweepTab
from .tabs.training import TrainingTab
from .tabs.live import LiveTab
from .tabs.charts import ChartsTab
from .tabs.model_lab import ModelLabTab

class ControlCenter(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=8)
        self.master = master
        self.pack(fill="both", expand=True)
        self.proc = ProcessRunner(RESULTS_DIR)
        self.accum = {}
        self.current_feats = []

        self._build_ui()
        self._load_params()

    def _build_ui(self):
        self.master.title("ElBotto – Control Center (PLUS)")
        self.master.geometry("1280x820")

        # Common params
        self.frm = ttk.LabelFrame(self, text="Common Parameters")
        self.frm.pack(fill="x")

        self.var_dataset   = tk.StringVar(value=DEFAULTS["dataset"])
        self.var_symbols   = tk.StringVar(value=DEFAULTS["symbols"])
        self.var_threshold = tk.DoubleVar(value=DEFAULTS["threshold"])
        self.var_capital   = tk.DoubleVar(value=DEFAULTS["capital"])
        self.var_maxpos    = tk.DoubleVar(value=DEFAULTS["max_position"])
        self.var_fee       = tk.DoubleVar(value=DEFAULTS["fee"])
        self.var_windows   = tk.StringVar(value=DEFAULTS["windows"])
        self.var_spread    = tk.StringVar(value=DEFAULTS["spread_max"])
        self.var_tp        = tk.StringVar(value=DEFAULTS["tp_bps"])
        self.var_sl        = tk.StringVar(value=DEFAULTS["sl_bps"])
        self.var_risk      = tk.StringVar(value=DEFAULTS["risk_per_trade"])
        self.var_extra     = tk.StringVar(value=DEFAULTS.get("extra_args",""))
        self.var_append_ind = tk.BooleanVar(value=DEFAULTS.get("append_indicators_flag", False))

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

        # tools row
        tools = ttk.Frame(self); tools.pack(fill="x", pady=6)
        ttk.Button(tools, text="Indicators…", command=self._open_indicators).pack(side="left", padx=4)
        ttk.Checkbutton(tools, text="Append selected indicators to args", variable=self.var_append_ind).pack(side="left", padx=4)
        ttk.Button(tools, text="Open Results", command=self._open_results).pack(side="right", padx=4)

        # Tabs
        self.nb = ttk.Notebook(self); self.nb.pack(fill="both", expand=True)
        self.var_analysis_script = tk.StringVar()
        self.var_backtest_script = tk.StringVar()
        self.var_train_script = tk.StringVar()
        self.var_paper_script = tk.StringVar()
        self.var_live_script = tk.StringVar()
        self.var_env = tk.StringVar(value="paper")
        self.var_api_key = tk.StringVar()
        self.var_api_secret = tk.StringVar()

        from .tabs.analysis import AnalysisTab
        self.tab_analysis = AnalysisTab(self.nb, self.var_analysis_script); self.nb.add(self.tab_analysis, text="Analysis")
        from .tabs.backtest import BacktestTab
        self.tab_backtest = BacktestTab(self.nb, self.var_backtest_script); self.nb.add(self.tab_backtest, text="Backtest")
        from .tabs.sweep import SweepTab
        self.tab_sweep = SweepTab(self.nb); self.nb.add(self.tab_sweep, text="Batch Sweep")
        from .tabs.data_sweep import DataSweepTab
        self.tab_data_sweep = DataSweepTab(self.nb); self.nb.add(self.tab_data_sweep, text="Data Sweep")
        from .tabs.training import TrainingTab
        self.tab_train = TrainingTab(self.nb, self.var_train_script); self.nb.add(self.tab_train, text="Training")
        from .tabs.live import LiveTab
        self.tab_live = LiveTab(self.nb, self.var_paper_script, self.var_live_script, self.var_env, self.var_api_key, self.var_api_secret); self.nb.add(self.tab_live, text="Paper/Live")
        from .tabs.charts import ChartsTab
        self.tab_charts = ChartsTab(self.nb); self.nb.add(self.tab_charts, text="Charts")
        from .tabs.model_lab import ModelLabTab
        self.tab_model = ModelLabTab(self.nb); self.nb.add(self.tab_model, text="Model Lab")

        # Output split
        split = ttk.PanedWindow(self, orient="vertical"); split.pack(fill="both", expand=True, pady=(6,0))
        self.metrics = __import__('elbotto_gui.widgets.metrics', fromlist=['MetricsPanel']).MetricsPanel(split)
        logf = ttk.LabelFrame(split, text="Log")
        self.txt = tk.Text(logf, wrap="word"); self.txt.pack(fill="both", expand=True, padx=6, pady=6)
        split.add(self.metrics, weight=1); split.add(logf, weight=2)

        # Bottom bar
        bar = ttk.Frame(self); bar.pack(fill="x", pady=6)
        self.btn_run = ttk.Button(bar, text="▶ Run", command=self._run_clicked); self.btn_run.pack(side="left", padx=6)
        self.btn_stop = ttk.Button(bar, text="■ Stop", command=self._stop_clicked, state="disabled"); self.btn_stop.pack(side="left", padx=6)
        self.status = ttk.Label(bar, text="Ready"); self.status.pack(side="right", padx=6)

        self.after(100, self._timer)

    def _pick_dataset(self):
        p = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV","*.csv"),("All","*.*")])
        if p: self.var_dataset.set(p)

    def _open_indicators(self):
        def on_change(selected, append_flag):
            self.current_indicators = selected
            self.var_append_ind.set(bool(append_flag))
            save_indicators(selected)
        IndicatorWindow(self.master, on_change=on_change)

    def _apply_preset(self, name):
        from .presets import PRESETS
        cfg = PRESETS[name]
        self.var_threshold.set(cfg["threshold"]); self.var_maxpos.set(cfg["max_position"]); self.var_fee.set(cfg["fee"]); self.var_windows.set(cfg["windows"])

    def _collect(self):
        return {
            "dataset": self.var_dataset.get(),
            "symbols": self.var_symbols.get(),
            "threshold": float(self.var_threshold.get()),
            "capital": float(self.var_capital.get()),
            "max_position": float(self.var_maxpos.get()),
            "fee": float(self.var_fee.get()),
            "windows": self.var_windows.get(),
            "spread_max": self.var_spread.get(),
            "tp_bps": self.var_tp.get(),
            "sl_bps": self.var_sl.get(),
            "risk_per_trade": self.var_risk.get(),
            "analysis_script": self.var_analysis_script.get() or "run_quickstart_tuned.py",
            "backtest_script": self.var_backtest_script.get() or "src\\elbotto\\backtest\\backtest.py",
            "train_script": self.var_train_script.get(),
            "paper_script": self.var_paper_script.get(),
            "live_script": self.var_live_script.get(),
            "env": self.var_env.get(),
            "api_key": self.var_api_key.get(),
            "api_secret": self.var_api_secret.get(),
            "extra_args": self.var_extra.get(),
            "append_indicators_flag": self.var_append_ind.get()
        }

    def _load_params(self):
        cfg = load_params()
        self.var_dataset.set(cfg.get("dataset"))
        self.var_symbols.set(cfg.get("symbols"))
        self.var_threshold.set(cfg.get("threshold",0.5))
        self.var_capital.set(cfg.get("capital",5000.0))
        self.var_maxpos.set(cfg.get("max_position",1.0))
        self.var_fee.set(cfg.get("fee",0.0002))
        self.var_windows.set(cfg.get("windows","3 6 9"))
        self.var_spread.set(cfg.get("spread_max",""))
        self.var_tp.set(cfg.get("tp_bps",""))
        self.var_sl.set(cfg.get("sl_bps",""))
        self.var_risk.set(cfg.get("risk_per_trade",""))
        self.var_analysis_script.set(cfg.get("analysis_script","run_quickstart_tuned.py"))
        self.var_backtest_script.set(cfg.get("backtest_script","src\\elbotto\\backtest\\backtest.py"))
        self.var_train_script.set(cfg.get("train_script","src\\elbotto\\ml\\train.py"))
        self.var_paper_script.set(cfg.get("paper_script","src\\elbotto\\bots\\paper.py"))
        self.var_live_script.set(cfg.get("live_script","src\\elbotto\\bots\\live.py"))
        self.var_env.set(cfg.get("env","paper"))
        self.var_api_key.set(cfg.get("api_key","")); self.var_api_secret.set(cfg.get("api_secret",""))
        self.var_extra.set(cfg.get("extra_args",""))
        self.var_append_ind.set(cfg.get("append_indicators_flag", False))
        self.current_indicators = load_indicators()

        # profiles
        names = sorted(load_profiles().keys())
        self.var_profile = tk.StringVar()
        self.cbo_profile = getattr(self, "cbo_profile", None)
        if not self.cbo_profile:
            tool = ttk.Frame(self); tool.pack_forget()
        # nothing more: profiles management will be added if needed

    def _save_params(self):
        save_params(self._collect())

    def _open_results(self):
        RESULTS_DIR.mkdir(exist_ok=True)
        try: os.startfile(RESULTS_DIR)
        except Exception: messagebox.showinfo("Results", str(RESULTS_DIR.resolve()))

    def _append(self, s): self.txt.insert("end", s); self.txt.see("end")

    def _build_args(self, script):
        args = [Path(".venv")/"Scripts"/"python.exe", script,
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
        if self.var_append_ind.get() and self.current_indicators:
            args += ["--indicators", *self.current_indicators]
        if self.var_extra.get().strip(): args += self.var_extra.get().split()
        return args

    def _run_clicked(self):
        if self.proc.proc and self.proc.proc.poll() is None:
            messagebox.showwarning("Busy", "Process already running."); return

        tab = self.nb.tab(self.nb.select(), "text")
        self.txt.delete("1.0","end"); self.accum = {}; self.current_feats = []
        self.btn_run.config(state="disabled"); self.btn_stop.config(state="normal")
        self.status.config(text="Running…")

        if tab == "Analysis":
            args = self._build_args(self.var_analysis_script.get() or "run_quickstart_tuned.py")
            env = os.environ.copy()
            self.proc.start(args, self._on_line, env)
        elif tab == "Backtest":
            args = self._build_args(self.var_backtest_script.get())
            env = os.environ.copy()
            self.proc.start(args, self._on_line, env)
        elif tab == "Batch Sweep":
            start = float(self.tab_sweep.var_start.get()); stop = float(self.tab_sweep.var_stop.get()); step = float(self.tab_sweep.var_step.get())
            thresholds = [round(start + i*step, 10) for i in range(int((stop-start)/step)+1)]
            base = self._build_args(self.var_analysis_script.get() or "run_quickstart_tuned.py")
            def run_sweep():
                for t in thresholds:
                    args = list(base)
                    for i, tok in enumerate(args):
                        if tok == "--threshold": args[i+1] = str(t); break
                    self._append(f"\n>> threshold={t}\n")
                    self.proc.start(args, self._on_line, os.environ.copy())
                    # wait loop
                    while True:
                        if self.proc.proc and self.proc.proc.poll() is not None: break
                        self.master.after(100, self.master.update())
                self._append("\n[SWEEP DONE]\n"); self.btn_run.config(state="normal"); self.btn_stop.config(state="disabled"); self.status.config(text="Finished")
            self.after(50, run_sweep)
        elif tab == "Data Sweep":
            files = self.tab_data_sweep.iter_files()
            base = self._build_args(self.var_analysis_script.get() or "run_quickstart_tuned.py")
            def run_files():
                for f in files:
                    chunks = list(self.tab_data_sweep.make_chunks(f))
                    for c in chunks:
                        args = list(base)
                        # replace dataset path
                        for i, tok in enumerate(args):
                            if tok == "--dataset":
                                args[i+1] = str(c); break
                        self._append(f"\n>> dataset={c}\n")
                        self.proc.start(args, self._on_line, os.environ.copy())
                        while True:
                            if self.proc.proc and self.proc.proc.poll() is not None: break
                            self.master.after(100, self.master.update())
                self._append("\n[DATA SWEEP DONE]\n"); self.btn_run.config(state="normal"); self.btn_stop.config(state="disabled"); self.status.config(text="Finished")
            self.after(50, run_files)
        elif tab == "Training":
            args = self._build_args(self.var_train_script.get()) + ["--epochs", str(self.tab_train.var_epochs.get()), "--lr", str(self.tab_train.var_lr.get()), "--val", str(self.tab_train.var_val.get())]
            self.proc.start(args, self._on_line, os.environ.copy())
        elif tab == "Paper/Live":
            script = self.var_paper_script.get() if self.var_env.get()=="paper" else self.var_live_script.get()
            args = self._build_args(script)
            env = os.environ.copy()
            if self.var_api_key.get(): env["BINANCE_API_KEY"] = self.var_api_key.get()
            if self.var_api_secret.get(): env["BINANCE_API_SECRET"] = self.var_api_secret.get()
            self.proc.start(args, self._on_line, env)
        elif tab == "Charts":
            # draw chart after a finished run
            from .tabs.charts import ChartsTab
            self.tab_charts.plot_features(self.current_feats)
            self.btn_run.config(state="normal"); self.btn_stop.config(state="disabled"); self.status.config(text="Ready")
        elif tab == "Model Lab":
            # call internal quick_models.py via separate console run
            csv_path = self.tab_model.var_csv.get()
            feats = self.tab_model.var_features.get().split()
            label = self.tab_model.var_label.get()
            model = self.tab_model.var_model.get()
            test_size = str(self.tab_model.var_test_size.get())
            cv = str(self.tab_model.var_cv.get())
            seed = str(self.tab_model.var_seed.get())
            script = "elbotto_gui/ml/quick_models.py"
            args = [Path(".venv")/"Scripts"/"python.exe", script, "--csv", csv_path, "--features", *feats, "--label", label, "--model", model, "--test-size", test_size, "--cv", cv, "--seed", seed]
            self.proc.start(args, self._on_line, os.environ.copy())

    def _on_line(self, line):
        self._append(line)
        parse_incremental(line, self.accum)
        self.metrics.update_metrics(self.accum)
        feats = self.accum.get("features", [])
        if feats:
            self.current_feats = feats
            self.metrics.set_features(feats)
        if line.startswith("[EXIT]"):
            try:
                if self.proc.log_path and self.proc.log_path.exists():
                    text = self.proc.log_path.read_text(encoding="utf-8")
                    m, feats = parse_full(text)
                    self.metrics.update_metrics(m)
                    if feats:
                        self.current_feats = feats
                        self.metrics.set_features(feats)
                    # save metrics csv
                    ts = self.proc.log_path.stem.replace("log_run_","")
                    out_csv = RESULTS_DIR / f"metrics_{ts}.csv"
                    with out_csv.open("w", newline="", encoding="utf-8") as f:
                        w = csv.writer(f); w.writerow(["metric","value"])
                        for k,v in m.items(): w.writerow([k,v])
                        if feats:
                            w.writerow([]); w.writerow(["feature","delta","sign"])
                            for n,val,sg in feats: w.writerow([n,val,sg])
                    # update "latest" pointer
                    (RESULTS_DIR/"metrics_latest_features.csv").write_text("feature,delta,sign\n" + "\n".join(f"{n},{val},{sg}" for n,val,sg in feats), encoding="utf-8")
                    self._append(f"\n[INFO] Saved metrics CSV: {out_csv}\n")
            except Exception as e:
                self._append(f"[WARN] finalize failed: {e!r}\n")
            self.btn_run.config(state="normal"); self.btn_stop.config(state="disabled"); self.status.config(text="Finished")

    def _stop_clicked(self):
        self.proc.terminate()
        self.btn_stop.config(state="disabled"); self.btn_run.config(state="normal")

    def _timer(self):
        self.after(200, self._timer)

def main():
    root = tk.Tk()
    ControlCenter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
