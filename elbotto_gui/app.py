from elbotto_gui.tabs.control_tab import ControlTab

import os, datetime, csv
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .storage import RESULTS_DIR, DEFAULTS, load_params, save_params, load_profiles, save_profiles
from .presets import PRESETS
from .runner import ProcessRunner
from .parsing import parse_incremental, parse_full
from .widgets.metrics import MetricsPanel
from .tabs.analysis import AnalysisTab
from .tabs.backtest import BacktestTab
from .tabs.sweep import SweepTab
from .tabs.training import TrainingTab
from .tabs.live import LiveTab

class ControlCenter(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=8)
        self.master = master
        self.pack(fill="both", expand=True)

        # State
        self.proc = ProcessRunner(RESULTS_DIR)
        self.accum_metrics = {}  # incremental parse
        self.current_log = None
        self.current_metrics_csv = None

        # Build UI
        self._build_ui()
        self._load_params()

    def _build_ui(self):
        self.master.title("ElBotto â€“ Control Center")
        self.master.geometry("1140x760")

        # Common params frame
        self.frm_params = ttk.LabelFrame(self, text="Common Parameters")
        self.frm_params.pack(fill="x")

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

        r=0
        ttk.Label(self.frm_params, text="Dataset:").grid(row=r, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(self.frm_params, textvariable=self.var_dataset, width=70).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self.frm_params, text="Browseâ€¦", command=self._pick_dataset).grid(row=r, column=2, padx=6)
        r+=1
        ttk.Label(self.frm_params, text="Symbols:").grid(row=r, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(self.frm_params, textvariable=self.var_symbols, width=40).grid(row=r, column=1, sticky="w", padx=6)
        ttk.Label(self.frm_params, text="Windows:").grid(row=r, column=2, sticky="e")
        ttk.Entry(self.frm_params, textvariable=self.var_windows, width=16).grid(row=r, column=3, sticky="w", padx=6)
        r+=1
        ttk.Label(self.frm_params, text="Threshold:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(self.frm_params, textvariable=self.var_threshold, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(self.frm_params, text="Capital:").grid(row=r, column=2, sticky="e")
        ttk.Entry(self.frm_params, textvariable=self.var_capital, width=12).grid(row=r, column=3, sticky="w", padx=6)
        r+=1
        ttk.Label(self.frm_params, text="Max pos:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(self.frm_params, textvariable=self.var_maxpos, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(self.frm_params, text="Fee:").grid(row=r, column=2, sticky="e")
        ttk.Entry(self.frm_params, textvariable=self.var_fee, width=10).grid(row=r, column=3, sticky="w", padx=6)
        r+=1
        ttk.Label(self.frm_params, text="Spread max:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(self.frm_params, textvariable=self.var_spread, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(self.frm_params, text="TP/SL (bps):").grid(row=r, column=2, sticky="e")
        fr = ttk.Frame(self.frm_params); fr.grid(row=r, column=3, sticky="w")
        ttk.Entry(fr, textvariable=self.var_tp, width=7).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left", padx=4)
        ttk.Entry(fr, textvariable=self.var_sl, width=7).pack(side="left")
        r+=1
        ttk.Label(self.frm_params, text="Risk per trade:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(self.frm_params, textvariable=self.var_risk, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(self.frm_params, text="Extra args:").grid(row=r, column=2, sticky="e")
        ttk.Entry(self.frm_params, textvariable=self.var_extra, width=30).grid(row=r, column=3, sticky="w", padx=6)

        for c in range(4): self.frm_params.grid_columnconfigure(c, weight=1)

        # Presets + profiles
        tool = ttk.Frame(self); tool.pack(fill="x", pady=6)
        ttk.Button(tool, text="Conservative", command=lambda:self._apply_preset("Conservative")).pack(side="left", padx=4)
        ttk.Button(tool, text="Default", command=lambda:self._apply_preset("Default")).pack(side="left", padx=4)
        ttk.Button(tool, text="Aggressive", command=lambda:self._apply_preset("Aggressive")).pack(side="left", padx=4)

        ttk.Label(tool, text="Profile:").pack(side="left", padx=(16,4))
        self.var_profile = tk.StringVar()
        self.cbo_profile = ttk.Combobox(tool, textvariable=self.var_profile, width=24, state="readonly")
        self.cbo_profile.pack(side="left")
        ttk.Button(tool, text="Save asâ€¦", command=self._save_profile).pack(side="left", padx=4)
        ttk.Button(tool, text="Load", command=self._load_profile).pack(side="left", padx=4)
        ttk.Button(tool, text="Open Results", command=self._open_results).pack(side="right", padx=4)

        # Tabs
        self.nb = ttk.Notebook(self); self.nb.pack(fill="both", expand=True)
        self.var_analysis_script = tk.StringVar()
        self.var_backtest_script = tk.StringVar()
        self.var_train_script    = tk.StringVar()
        self.var_paper_script    = tk.StringVar()
        self.var_live_script     = tk.StringVar()
        self.var_env             = tk.StringVar(value="paper")
        self.var_api_key         = tk.StringVar()
        self.var_api_secret      = tk.StringVar()

        self.tab_analysis = AnalysisTab(self.nb, self.var_analysis_script); self.nb.add(self.tab_analysis, text="Analysis")
        self.tab_backtest = BacktestTab(self.nb, self.var_backtest_script); self.nb.add(self.tab_backtest, text="Backtest")
        self.tab_sweep    = SweepTab(self.nb); self.nb.add(self.tab_sweep, text="Batch Sweep")
        self.tab_train    = TrainingTab(self.nb, self.var_train_script); self.nb.add(self.tab_train, text="Training")
        self.tab_live     = LiveTab(self.nb, self.var_paper_script, self.var_live_script, self.var_env, self.var_api_key, self.var_api_secret); self.nb.add(self.tab_live, text="Paper/Live")

        # Output split: metrics + log
        split = ttk.PanedWindow(self, orient="vertical"); split.pack(fill="both", expand=True, pady=(6,0))
        self.metrics = MetricsPanel(split)
        logf = ttk.LabelFrame(split, text="Log")
        self.txt = tk.Text(logf, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=6, pady=6)
        split.add(self.metrics, weight=1); split.add(logf, weight=2)

        # Bottom bar
        bar = ttk.Frame(self); bar.pack(fill="x", pady=6)
        self.btn_run = ttk.Button(bar, text="â–¶ Run", command=self._run_clicked); self.btn_run.pack(side="left", padx=6)
        self.btn_stop = ttk.Button(bar, text="â–  Stop", command=self._stop_clicked, state="disabled"); self.btn_stop.pack(side="left", padx=6)
        self.status = ttk.Label(bar, text="Ready"); self.status.pack(side="right", padx=6)

        self.after(100, self._poll)

    # ---- util ----
    def _pick_dataset(self):
        p = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV","*.csv"),("All","*.*")])
        if p: self.var_dataset.set(p)

    def _apply_preset(self, name):
        cfg = PRESETS[name]
        self.var_threshold.set(cfg["threshold"])
        self.var_maxpos.set(cfg["max_position"])
        self.var_fee.set(cfg["fee"])
        self.var_windows.set(cfg["windows"])

    def _collect_params(self):
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
            "analysis_script": self.var_analysis_script.get(),
            "backtest_script": self.var_backtest_script.get(),
            "train_script": self.var_train_script.get(),
            "paper_script": self.var_paper_script.get(),
            "live_script": self.var_live_script.get(),
            "env": self.var_env.get(),
            "api_key": self.var_api_key.get(),
            "api_secret": self.var_api_secret.get(),
            "extra_args": self.var_extra.get()
        }

    def _load_params(self):
        p = load_params()
        self.var_dataset.set(p.get("dataset"))
        self.var_symbols.set(p.get("symbols"))
        self.var_threshold.set(p.get("threshold", 0.5))
        self.var_capital.set(p.get("capital", 5000.0))
        self.var_maxpos.set(p.get("max_position", 1.0))
        self.var_fee.set(p.get("fee", 0.0002))
        self.var_windows.set(p.get("windows", "3 6 9"))
        self.var_spread.set(p.get("spread_max", ""))
        self.var_tp.set(p.get("tp_bps", ""))
        self.var_sl.set(p.get("sl_bps", ""))
        self.var_risk.set(p.get("risk_per_trade", ""))
        self.var_analysis_script.set(p.get("analysis_script"))
        self.var_backtest_script.set(p.get("backtest_script"))
        self.var_train_script.set(p.get("train_script"))
        self.var_paper_script.set(p.get("paper_script"))
        self.var_live_script.set(p.get("live_script"))
        self.var_env.set(p.get("env","paper"))
        self.var_api_key.set(p.get("api_key",""))
        self.var_api_secret.set(p.get("api_secret",""))
        self.var_extra.set(p.get("extra_args",""))

        # load profiles list
        profiles = load_profiles()
        names = sorted(profiles.keys())
        self.cbo_profile["values"] = names
        if names: self.cbo_profile.current(0)

    def _save_params(self):
        save_params(self._collect_params())

    def _save_profile(self):
        name = tk.simpledialog.askstring("Save profile", "Profile name:")
        if not name: return
        profiles = load_profiles()
        profiles[name] = self._collect_params()
        save_profiles(profiles)
        self.cbo_profile["values"] = sorted(profiles.keys())
        self.cbo_profile.set(name)
        messagebox.showinfo("Profile", f"Saved profile '{name}'.")

    def _load_profile(self):
        name = self.var_profile.get()
        if not name: return
        profiles = load_profiles()
        if name in profiles:
            p = profiles[name]
            save_params(p)  # also set as current
            self._load_params()

    def _open_results(self):
        RESULTS_DIR.mkdir(exist_ok=True)
        try:
            os.startfile(RESULTS_DIR)
        except Exception:
            messagebox.showinfo("Results", f"Results in {RESULTS_DIR.resolve()}")

    def _append(self, s: str):
        self.txt.insert("end", s)
        self.txt.see("end")

    # ---- run logic ----
    def _build_base_args(self, script_path: str):
        args = [
            Path(".venv")/"Scripts"/"python.exe",
            script_path,
            "--dataset", self.var_dataset.get(),
            "--threshold", str(self.var_threshold.get()),
            "--capital", str(self.var_capital.get()),
            "--max-position", str(self.var_maxpos.get()),
            "--fee", str(self.var_fee.get()),
            "--windows", *self.var_windows.get().split()
        ]
        if self.var_symbols.get().strip():
            args += ["--symbols", *self.var_symbols.get().split()]
        if self.var_spread.get():
            args += ["--spread-max", str(self.var_spread.get())]
        if self.var_tp.get():
            args += ["--take-profit-bps", str(self.var_tp.get())]
        if self.var_sl.get():
            args += ["--stop-loss-bps", str(self.var_sl.get())]
        if self.var_risk.get():
            args += ["--risk-per-trade", str(self.var_risk.get())]
        if self.var_extra.get().strip():
            # naive split by spaces; user can enter extra flags as needed
            args += self.var_extra.get().split()
        return args

    def _run_clicked(self):
        if self.proc.proc and self.proc.proc.poll() is None:
            messagebox.showwarning("Busy", "Process already running.")
            return
        tab = self.nb.tab(self.nb.select(), "text")
        self.accum_metrics = {}
        self.txt.delete("1.0", "end")
        self.status.config(text="Runningâ€¦")
        self.btn_run.config(state="disabled"); self.btn_stop.config(state="normal")

        if tab == "Analysis":
            script = self.var_analysis_script.get() or "run_quickstart_tuned.py"
            args = self._build_base_args(script)
            env = os.environ.copy()
        elif tab == "Backtest":
            script = self.var_backtest_script.get()
            args = self._build_base_args(script)
            env = os.environ.copy()
        elif tab == "Training":
            script = self.var_train_script.get()
            args = self._build_base_args(script) + ["--epochs", str(self.tab_train.var_epochs.get()), "--lr", str(self.tab_train.var_lr.get()), "--val", str(self.tab_train.var_val.get())]
            env = os.environ.copy()
        elif tab == "Batch Sweep":
            # Iterate thresholds synchronously
            start = float(self.tab_sweep.var_start.get()); stop = float(self.tab_sweep.var_stop.get()); step = float(self.tab_sweep.var_step.get())
            thresholds = [round(start + i*step, 10) for i in range(int((stop-start)/step)+1)]
            script = self.var_analysis_script.get() or "run_quickstart_tuned.py"
            base = self._build_base_args(script)
            def run_sweep():
                for t in thresholds:
                    args = list(base)
                    for i, tok in enumerate(args):
                        if tok == "--threshold": args[i+1] = str(t); break
                    self._append(f"\n>> threshold={t}\n")
                    self.proc.start(args, self._on_line)
                    # busy-wait until exits
                    while True:
                        if self.proc.proc and self.proc.proc.poll() is not None: break
                        self.master.after(200, self.master.update())
                self._append("\n[SWEEP DONE]\n")
                self.status.config(text="Finished"); self.btn_run.config(state="normal"); self.btn_stop.config(state="disabled")
            self.after(50, run_sweep)
            return
        else:  # Paper/Live
            script = self.var_paper_script.get() if self.var_env.get()=="paper" else self.var_live_script.get()
            args = self._build_base_args(script)
            env = os.environ.copy()
            if self.var_api_key.get(): env["BINANCE_API_KEY"] = self.var_api_key.get()
            if self.var_api_secret.get(): env["BINANCE_API_SECRET"] = self.var_api_secret.get()

        self.proc.start(args, self._on_line, env)

    def _on_line(self, line: str):
        self._append(line)
        parse_incremental(line, self.accum_metrics)
        self.metrics.update_metrics(self.accum_metrics)
        # update features in real-time when "+" or "-" lines appear
        feats = self.accum_metrics.get("features", [])
        if feats: self.metrics.set_features(feats)

        if line.startswith("[EXIT]"):
            # finalize
            try:
                if self.proc.log_path and self.proc.log_path.exists():
                    text = self.proc.log_path.read_text(encoding="utf-8")
                    m, feats = parse_full(text)
                    self.metrics.update_metrics(m)
                    self.metrics.set_features(feats)
                    # save metrics CSV
                    ts = self.proc.log_path.stem.replace("log_run_","")
                    out_csv = RESULTS_DIR / f"metrics_{ts}.csv"
                    with out_csv.open("w", newline="", encoding="utf-8") as f:
                        wr = csv.writer(f)
                        wr.writerow(["metric","value"])
                        for k,v in m.items(): wr.writerow([k,v])
                        if feats:
                            wr.writerow([]); wr.writerow(["feature","delta","sign"])
                            for name, val, sign in feats:
                                wr.writerow([name, val, sign])
                    self._append(f"\n[INFO] Saved metrics CSV: {out_csv}\n")
            except Exception as e:
                self._append(f"[WARN] finalize failed: {e!r}\n")

            self.status.config(text="Finished"); self.btn_run.config(state="normal"); self.btn_stop.config(state="disabled")

    def _stop_clicked(self):
        self.proc.terminate()
        self.btn_stop.config(state="disabled"); self.btn_run.config(state="normal")

    def _poll(self):
        # placeholder for timers if needed later
        self.after(200, self._poll)

def main():
    root = tk.Tk()
    ControlCenter(root)
    root.mainloop()

if __name__ == "__main__":
    main()

        self.nb.add(ControlTab(self.nb), text="Control")
