
# gui_runner_max.py — zaawansowane GUI do ElBotto
# Funkcje:
# - Wspólne parametry (dataset, symbols, threshold, windows, capital, max-position, fee, spread_max, TP/SL, risk_per_trade)
# - Presety Conservative / Default / Aggressive
# - Zakładki: Analysis, Backtest, Batch Sweep, Training, Paper/Live
# - Log na żywo, automatyczny zapis do results/log_*.txt
# - Parsowanie metryk z konsoli i prezentacja "Aktualne wartości" + tabela cech (ΔPnL)
# - Zapis metryk do CSV: results/metrics_*.csv
# - Zapis/odczyt wszystkich parametrów do JSON: results/gui_params.json
#
# Uwaga: GUI wywołuje istniejące skrypty w repo. Jeśli nazwy są inne, wskaż je w polach "Browse…".

import json, subprocess, threading, queue, re, csv, datetime, os, sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "ElBotto – Control Center (GUI)"
RESULTS_DIR = Path("results")
PARAMS_JSON = RESULTS_DIR / "gui_params.json"

DEFAULTS = {
    "dataset": "data\\binance_order_book_small.csv",
    "symbols": "BTCUSDT ETHUSDT",
    "threshold": 0.50,
    "capital": 5000.0,
    "max_position": 1.0,
    "fee": 0.0002,
    "windows": "3 6 9",
    "spread_max": "",
    "tp_bps": "",
    "sl_bps": "",
    "risk_per_trade": "",
    "analysis_script": "run_quickstart_tuned.py",
    "backtest_script": "src\\elbotto\\backtest\\backtest.py",
    "train_script": "src\\elbotto\\ml\\train.py",
    "paper_script": "src\\elbotto\\bots\\paper.py",
    "live_script": "src\\elbotto\\bots\\live.py",
    "api_key": "",
    "api_secret": "",
    "env": "paper"
}

PRESETS = {
    "Conservative": {"threshold": 0.60, "max_position": 0.8, "fee": 0.0004, "windows": "5 10 20"},
    "Default": {"threshold": 0.50, "max_position": 1.0, "fee": 0.0002, "windows": "3 6 9"},
    "Aggressive": {"threshold": 0.40, "max_position": 2.0, "fee": 0.0001, "windows": "2 4 8"}
}

def load_params():
    try:
        if PARAMS_JSON.exists():
            return json.loads(PARAMS_JSON.read_text(encoding="utf-8"))
    except Exception:
        pass
    return DEFAULTS.copy()

def save_params(p):
    RESULTS_DIR.mkdir(exist_ok=True, parents=True)
    PARAMS_JSON.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")

def parse_stdout_to_metrics(text:str):
    """Parsuje podstawowe metryki i cechy ΔPnL z tekstu wyjścia."""
    metrics = {}
    feats = []
    # Final capital per symbol
    for m in re.finditer(r"===\s*([A-Z]+)\s*===\s*[\r\n]+Transakcji:\s*(\d+),\s*końcowy kapitał:\s*([0-9.]+)", text, re.IGNORECASE):
        sym, trades, capital = m.group(1), int(m.group(2)), float(m.group(3))
        metrics[f"{sym}_trades"] = trades
        metrics[f"{sym}_final_capital"] = capital
    # Feature importances
    for m in re.finditer(r"([+−\-])\s*([a-zA-Z0-9_]+):\s*ΔPnL\s*=\s*([\-0-9.]+)", text):
        sign, name, val = m.group(1), m.group(2), float(m.group(3))
        feats.append((name, val, sign))
    return metrics, feats

class ControlCenter(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=8)
        self.master = master
        self.pack(fill="both", expand=True)
        self.proc = None
        self.q = queue.Queue()
        self._build_ui()
        self._load_params()

    # ---------------- UI ----------------
    def _build_ui(self):
        self.master.title(APP_TITLE)
        self.master.geometry("1080x760")

        # Notebook
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True)

        self.tab_analysis = ttk.Frame(self.nb); self.nb.add(self.tab_analysis, text="Analysis")
        self.tab_backtest = ttk.Frame(self.nb); self.nb.add(self.tab_backtest, text="Backtest")
        self.tab_sweep = ttk.Frame(self.nb); self.nb.add(self.tab_sweep, text="Batch Sweep")
        self.tab_train = ttk.Frame(self.nb); self.nb.add(self.tab_train, text="Training")
        self.tab_live = ttk.Frame(self.nb); self.nb.add(self.tab_live, text="Paper/Live")

        # Common params
        self._build_common()

        # Tabs
        self._build_tab_analysis()
        self._build_tab_backtest()
        self._build_tab_sweep()
        self._build_tab_train()
        self._build_tab_live()

        # Output + metrics
        out = ttk.PanedWindow(self, orient="vertical"); out.pack(fill="both", expand=True, pady=(6,0))

        # Metrics frame
        self.metrics_frame = ttk.LabelFrame(out, text="Aktualne wartości")
        self._build_metrics(self.metrics_frame)

        # Log frame
        self.log_frame = ttk.LabelFrame(out, text="Log")
        self.txt = tk.Text(self.log_frame, wrap="word")
        self.txt.pack(fill="both", expand=True, padx=6, pady=6)

        out.add(self.metrics_frame, weight=1)
        out.add(self.log_frame, weight=2)

        # Bottom bar
        bar = ttk.Frame(self); bar.pack(fill="x", pady=6)
        ttk.Button(bar, text="Open Results", command=self._open_results).pack(side="left", padx=6)
        ttk.Button(bar, text="Save params", command=self._save_params).pack(side="left", padx=6)
        ttk.Button(bar, text="Load params", command=self._load_params).pack(side="left", padx=6)
        self.btn_run = ttk.Button(bar, text="▶ Run", command=self._run_clicked); self.btn_run.pack(side="left", padx=6)
        self.btn_stop = ttk.Button(bar, text="■ Stop", command=self._stop_clicked, state="disabled"); self.btn_stop.pack(side="left", padx=6)
        self.status = ttk.Label(bar, text="Ready"); self.status.pack(side="right", padx=6)

        self.after(100, self._pump_queue)

    def _build_common(self):
        f = ttk.LabelFrame(self, text="Wspólne parametry")
        f.pack(fill="x", pady=(6,0))

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

        r=0
        ttk.Label(f, text="Dataset:").grid(row=r, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(f, textvariable=self.var_dataset, width=70).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(f, text="Browse…", command=self._pick_dataset).grid(row=r, column=2, padx=6)
        r+=1
        ttk.Label(f, text="Symbols:").grid(row=r, column=0, sticky="w", padx=6, pady=4)
        ttk.Entry(f, textvariable=self.var_symbols, width=40).grid(row=r, column=1, sticky="w", padx=6)
        ttk.Label(f, text="Windows:").grid(row=r, column=2, sticky="e")
        ttk.Entry(f, textvariable=self.var_windows, width=18).grid(row=r, column=3, sticky="w", padx=6)
        r+=1
        ttk.Label(f, text="Threshold:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(f, textvariable=self.var_threshold, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(f, text="Capital:").grid(row=r, column=2, sticky="e")
        ttk.Entry(f, textvariable=self.var_capital, width=12).grid(row=r, column=3, sticky="w", padx=6)
        r+=1
        ttk.Label(f, text="Max pos:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(f, textvariable=self.var_maxpos, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(f, text="Fee:").grid(row=r, column=2, sticky="e")
        ttk.Entry(f, textvariable=self.var_fee, width=10).grid(row=r, column=3, sticky="w", padx=6)
        r+=1
        ttk.Label(f, text="Spread max:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(f, textvariable=self.var_spread, width=10).grid(row=r, column=1, sticky="w")
        ttk.Label(f, text="TP/SL (bps):").grid(row=r, column=2, sticky="e")
        fr = ttk.Frame(f); fr.grid(row=r, column=3, sticky="w")
        ttk.Entry(fr, textvariable=self.var_tp, width=7).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left", padx=4)
        ttk.Entry(fr, textvariable=self.var_sl, width=7).pack(side="left")
        r+=1
        ttk.Label(f, text="Risk per trade:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(f, textvariable=self.var_risk, width=10).grid(row=r, column=1, sticky="w")

        # Presets
        pres = ttk.LabelFrame(self, text="Presety")
        pres.pack(fill="x", pady=4)
        ttk.Button(pres, text="Conservative", command=lambda:self._apply_preset("Conservative")).pack(side="left", padx=6, pady=4)
        ttk.Button(pres, text="Default", command=lambda:self._apply_preset("Default")).pack(side="left", padx=6, pady=4)
        ttk.Button(pres, text="Aggressive", command=lambda:self._apply_preset("Aggressive")).pack(side="left", padx=6, pady=4)

    def _build_tab_analysis(self):
        f = ttk.LabelFrame(self.tab_analysis, text="Analysis")
        f.pack(fill="x", padx=6, pady=6)
        self.var_analysis_script = tk.StringVar(value=DEFAULTS["analysis_script"])
        ttk.Label(f, text="Script:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(f, textvariable=self.var_analysis_script, width=60).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Button(f, text="Browse…", command=lambda:self._pick_script(self.var_analysis_script)).grid(row=0, column=2, padx=6)

    def _build_tab_backtest(self):
        f = ttk.LabelFrame(self.tab_backtest, text="Backtest")
        f.pack(fill="x", padx=6, pady=6)
        self.var_backtest_script = tk.StringVar(value=DEFAULTS["backtest_script"])
        ttk.Label(f, text="Script:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(f, textvariable=self.var_backtest_script, width=60).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Button(f, text="Browse…", command=lambda:self._pick_script(self.var_backtest_script)).grid(row=0, column=2, padx=6)

    def _build_tab_sweep(self):
        f = ttk.LabelFrame(self.tab_sweep, text="Batch Sweep po threshold")
        f.pack(fill="x", padx=6, pady=6)
        self.var_sw_start = tk.DoubleVar(value=0.30)
        self.var_sw_stop  = tk.DoubleVar(value=0.65)
        self.var_sw_step  = tk.DoubleVar(value=0.05)
        ttk.Label(f, text="Start / Stop / Step:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        fr = ttk.Frame(f); fr.grid(row=0, column=1, sticky="w")
        ttk.Entry(fr, textvariable=self.var_sw_start, width=8).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left")
        ttk.Entry(fr, textvariable=self.var_sw_stop, width=8).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left")
        ttk.Entry(fr, textvariable=self.var_sw_step, width=8).pack(side="left")

    def _build_tab_train(self):
        f = ttk.LabelFrame(self.tab_train, text="Training (uczenie)")
        f.pack(fill="x", padx=6, pady=6)
        self.var_train_script = tk.StringVar(value=DEFAULTS["train_script"])
        ttk.Label(f, text="Train script:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(f, textvariable=self.var_train_script, width=60).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Button(f, text="Browse…", command=lambda:self._pick_script(self.var_train_script)).grid(row=0, column=2, padx=6)
        # basic training params
        self.var_epochs = tk.IntVar(value=50)
        self.var_lr     = tk.DoubleVar(value=1e-3)
        self.var_val    = tk.DoubleVar(value=0.2)
        ttk.Label(f, text="Epochs / LR / Val split:").grid(row=1, column=0, sticky="w", padx=6)
        fr = ttk.Frame(f); fr.grid(row=1, column=1, sticky="w")
        ttk.Entry(fr, textvariable=self.var_epochs, width=6).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left", padx=4)
        ttk.Entry(fr, textvariable=self.var_lr, width=10).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left", padx=4)
        ttk.Entry(fr, textvariable=self.var_val, width=6).pack(side="left")

    def _build_tab_live(self):
        f = ttk.LabelFrame(self.tab_live, text="Paper/Live (ostrożnie z kluczami!)")
        f.pack(fill="x", padx=6, pady=6)
        self.var_env = tk.StringVar(value=DEFAULTS["env"])
        ttk.Radiobutton(f, text="Paper", variable=self.var_env, value="paper").pack(side="left", padx=6)
        ttk.Radiobutton(f, text="Live", variable=self.var_env, value="live").pack(side="left", padx=6)

        self.var_paper_script = tk.StringVar(value=DEFAULTS["paper_script"])
        self.var_live_script  = tk.StringVar(value=DEFAULTS["live_script"])
        row=1
        ttk.Label(f, text="Paper script:").grid(row=row, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(f, textvariable=self.var_paper_script, width=60).grid(row=row, column=1, sticky="we", padx=6)
        ttk.Button(f, text="Browse…", command=lambda:self._pick_script(self.var_paper_script)).grid(row=row, column=2, padx=6)
        row+=1
        ttk.Label(f, text="Live script:").grid(row=row, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(f, textvariable=self.var_live_script, width=60).grid(row=row, column=1, sticky="we", padx=6)
        ttk.Button(f, text="Browse…", command=lambda:self._pick_script(self.var_live_script)).grid(row=row, column=2, padx=6)
        row+=1

        self.var_api_key = tk.StringVar(value=DEFAULTS["api_key"])
        self.var_api_secret = tk.StringVar(value=DEFAULTS["api_secret"])
        ttk.Label(f, text="API Key:").grid(row=row, column=0, sticky="e", padx=6)
        ttk.Entry(f, textvariable=self.var_api_key, width=40, show="•").grid(row=row, column=1, sticky="w", padx=6)
        row+=1
        ttk.Label(f, text="API Secret:").grid(row=row, column=0, sticky="e", padx=6)
        ttk.Entry(f, textvariable=self.var_api_secret, width=40, show="•").grid(row=row, column=1, sticky="w", padx=6)

    def _build_metrics(self, parent):
        # labels for key metrics
        grid = ttk.Frame(parent); grid.pack(fill="x", padx=6, pady=6)
        self.var_btc_trades = tk.StringVar(value="-")
        self.var_btc_cap    = tk.StringVar(value="-")
        self.var_eth_trades = tk.StringVar(value="-")
        self.var_eth_cap    = tk.StringVar(value="-")
        ttk.Label(grid, text="BTC trades/capital:").grid(row=0, column=0, sticky="w")
        ttk.Label(grid, textvariable=self.var_btc_trades).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(grid, textvariable=self.var_btc_cap).grid(row=0, column=2, sticky="w", padx=6)
        ttk.Label(grid, text="ETH trades/capital:").grid(row=1, column=0, sticky="w")
        ttk.Label(grid, textvariable=self.var_eth_trades).grid(row=1, column=1, sticky="w", padx=6)
        ttk.Label(grid, textvariable=self.var_eth_cap).grid(row=1, column=2, sticky="w", padx=6)

        # feature table
        self.tv = ttk.Treeview(parent, columns=("feature","delta","sign"), show="headings", height=8)
        self.tv.heading("feature", text="Feature")
        self.tv.heading("delta", text="ΔPnL")
        self.tv.heading("sign", text="+/-")
        self.tv.pack(fill="both", expand=True, padx=6, pady=6)

    # ------------- Utility -------------
    def _apply_preset(self, name):
        cfg = PRESETS[name]
        self.var_threshold.set(cfg["threshold"])
        self.var_maxpos.set(cfg["max_position"])
        self.var_fee.set(cfg["fee"])
        self.var_windows.set(cfg["windows"])

    def _pick_dataset(self):
        p = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV","*.csv"), ("All","*.*")])
        if p: self.var_dataset.set(p)

    def _pick_script(self, var):
        p = filedialog.askopenfilename(title="Select Python script", filetypes=[("Python","*.py"), ("All","*.*")])
        if p: var.set(p)

    def _collect_common(self):
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
            "analysis_script": getattr(self, "var_analysis_script", tk.StringVar(value=DEFAULTS["analysis_script"])).get(),
            "backtest_script": getattr(self, "var_backtest_script", tk.StringVar(value=DEFAULTS["backtest_script"])).get(),
            "train_script": getattr(self, "var_train_script", tk.StringVar(value=DEFAULTS["train_script"])).get(),
            "paper_script": getattr(self, "var_paper_script", tk.StringVar(value=DEFAULTS["paper_script"])).get(),
            "live_script": getattr(self, "var_live_script", tk.StringVar(value=DEFAULTS["live_script"])).get(),
            "env": getattr(self, "var_env", tk.StringVar(value="paper")).get(),
            "api_key": getattr(self, "var_api_key", tk.StringVar(value="")).get(),
            "api_secret": getattr(self, "var_api_secret", tk.StringVar(value="")).get(),
        }

    def _save_params(self):
        save_params(self._collect_common())
        messagebox.showinfo(APP_TITLE, "Parameters saved.")

    def _load_params(self):
        cfg = load_params()
        self.var_dataset.set(cfg.get("dataset", DEFAULTS["dataset"]))
        self.var_symbols.set(cfg.get("symbols", DEFAULTS["symbols"]))
        self.var_threshold.set(cfg.get("threshold", DEFAULTS["threshold"]))
        self.var_capital.set(cfg.get("capital", DEFAULTS["capital"]))
        self.var_maxpos.set(cfg.get("max_position", DEFAULTS["max_position"]))
        self.var_fee.set(cfg.get("fee", DEFAULTS["fee"]))
        self.var_windows.set(cfg.get("windows", DEFAULTS["windows"]))
        self.var_spread.set(cfg.get("spread_max", DEFAULTS["spread_max"]))
        self.var_tp.set(cfg.get("tp_bps", DEFAULTS["tp_bps"]))
        self.var_sl.set(cfg.get("sl_bps", DEFAULTS["sl_bps"]))
        self.var_risk.set(cfg.get("risk_per_trade", DEFAULTS["risk_per_trade"]))
        # optional scripts and creds
        self.var_analysis_script = tk.StringVar(value=cfg.get("analysis_script", DEFAULTS["analysis_script"]))
        self.var_backtest_script = tk.StringVar(value=cfg.get("backtest_script", DEFAULTS["backtest_script"]))
        self.var_train_script    = tk.StringVar(value=cfg.get("train_script", DEFAULTS["train_script"]))
        self.var_paper_script    = tk.StringVar(value=cfg.get("paper_script", DEFAULTS["paper_script"]))
        self.var_live_script     = tk.StringVar(value=cfg.get("live_script", DEFAULTS["live_script"]))
        self.var_env             = tk.StringVar(value=cfg.get("env", DEFAULTS["env"]))
        self.var_api_key         = tk.StringVar(value=cfg.get("api_key", ""))
        self.var_api_secret      = tk.StringVar(value=cfg.get("api_secret", ""))

    def _open_results(self):
        RESULTS_DIR.mkdir(exist_ok=True)
        try:
            os.startfile(RESULTS_DIR)
        except Exception:
            messagebox.showinfo(APP_TITLE, f"Results in: {RESULTS_DIR.resolve()}")

    def _append(self, text):
        self.txt.insert("end", text)
        self.txt.see("end")

    # ---------------- Run logic ----------------
    def _run_clicked(self):
        if self.proc and self.proc.poll() is None:
            messagebox.showwarning(APP_TITLE, "Process already running.")
            return

        RESULTS_DIR.mkdir(exist_ok=True, parents=True)
        tab = self.nb.tab(self.nb.select(), "text")
        cfg = self._collect_common()

        if tab == "Analysis":
            script = cfg["analysis_script"]
        elif tab == "Backtest":
            script = cfg["backtest_script"]
        elif tab == "Training":
            script = cfg["train_script"]
        else:  # Paper/Live or Sweep uses analysis script
            script = cfg["analysis_script"]

        # base args
        args = [
            Path(".venv")/"Scripts"/"python.exe",
            script,
            "--dataset", cfg["dataset"],
            "--threshold", str(cfg["threshold"]),
            "--capital", str(cfg["capital"]),
            "--max-position", str(cfg["max_position"]),
            "--fee", str(cfg["fee"]),
            "--windows", *cfg["windows"].split()
        ]
        if cfg["symbols"].strip():
            args += ["--symbols", *cfg["symbols"].split()]
        if cfg["spread_max"]:
            args += ["--spread-max", str(cfg["spread_max"])]
        if cfg["tp_bps"]:
            args += ["--take-profit-bps", str(cfg["tp_bps"])]
        if cfg["sl_bps"]:
            args += ["--stop-loss-bps", str(cfg["sl_bps"])]
        if cfg["risk_per_trade"]:
            args += ["--risk-per-trade", str(cfg["risk_per_trade"])]

        if tab == "Batch Sweep":
            start = float(self.var_sw_start.get())
            stop  = float(self.var_sw_stop.get())
            step  = float(self.var_sw_step.get())
            thresholds = [round(start + i*step, 10) for i in range(int((stop-start)/step)+1)]
            self._append(f">> Sweep thresholds: {thresholds}\n")
            threading.Thread(target=self._run_sweep, args=(args, thresholds), daemon=True).start()
            self.btn_run.config(state="disabled"); self.btn_stop.config(state="normal")
            return

        if tab == "Paper/Live":
            # użyj odpowiedniego skryptu i przekaż klucze w env
            script = cfg["paper_script"] if cfg["env"] == "paper" else cfg["live_script"]
            args = [Path(".venv")/"Scripts"/"python.exe", script] + args[2:]
            env = os.environ.copy()
            if cfg["api_key"]: env["BINANCE_API_KEY"] = cfg["api_key"]
            if cfg["api_secret"]: env["BINANCE_API_SECRET"] = cfg["api_secret"]
            self._start_process(args, extra_env=env)
        elif tab == "Training":
            # dodaj parametry trenowania jeśli skrypt je rozpoznaje
            args += ["--epochs", str(self.var_epochs.get()), "--lr", str(self.var_lr.get()), "--val", str(self.var_val.get())]
            self._start_process(args)
        else:
            self._start_process(args)

    def _run_sweep(self, base_args, thresholds):
        for t in thresholds:
            args = list(base_args)
            for i in range(len(args)-1):
                if args[i] == "--threshold":
                    args[i+1] = str(t); break
            self._append(f"\n>> Running threshold={t}\n")
            self._start_process(args, wait=True, csv_suffix=f"sweep_{t}")

        self._append("\n[SWEET DONE]\n")
        self.btn_run.config(state="normal"); self.btn_stop.config(state="disabled")

    def _start_process(self, args, wait=False, csv_suffix="run", extra_env=None):
        self.btn_run.config(state="disabled"); self.btn_stop.config(state="normal")
        self.status.config(text="Running…")
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        self.current_txt = RESULTS_DIR / f"log_{csv_suffix}_{ts}.txt"
        self.current_csv = RESULTS_DIR / f"metrics_{csv_suffix}_{ts}.csv"
        self._append(">> " + " ".join([str(a) for a in args]) + "\n\n")

        def worker():
            try:
                env = os.environ.copy()
                if extra_env: env.update(extra_env)
                self.proc = subprocess.Popen([str(a) for a in args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
                for line in self.proc.stdout:
                    self.q.put(line)
                self.proc.wait()
                self.q.put(f"[EXIT] {self.proc.returncode}\n")
            except FileNotFoundError:
                self.q.put("[ERROR] .venv\\Scripts\\python.exe not found. Run setup_env.bat first.\n")
            except Exception as e:
                self.q.put(f"[ERROR] {e!r}\n")

        threading.Thread(target=worker, daemon=True).start()

        if wait:
            # synchronous wait to parse right after
            while True:
                try:
                    line = self.q.get(timeout=0.1)
                    self._handle_line(line)
                    if line.startswith("[EXIT]"):
                        break
                except queue.Empty:
                    pass
            self._finalize_run()
        else:
            # async, handled by _pump_queue
            pass

    def _stop_clicked(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.btn_stop.config(state="disabled"); self.btn_run.config(state="normal")

    def _pump_queue(self):
        try:
            while True:
                line = self.q.get_nowait()
                self._handle_line(line)
        except queue.Empty:
            pass
        self.after(100, self._pump_queue)

    def _handle_line(self, line):
        # write to text
        self._append(line)
        if getattr(self, "current_txt", None):
            with self.current_txt.open("a", encoding="utf-8") as f:
                f.write(line)

        # Try to update metrics live
        try:
            txt = line
            # BTC / ETH current updates
            m = re.search(r"===\s*(BTCUSDT|ETHUSDT)\s*===", txt)
            if m:
                # do nothing here, handled on finalize
                pass
        except Exception:
            pass

        if line.startswith("[EXIT]"):
            self._finalize_run()

    def _finalize_run(self):
        # parse entire log file into metrics
        try:
            txt = self.current_txt.read_text(encoding="utf-8") if getattr(self, "current_txt", None) and self.current_txt.exists() else ""
            metrics, feats = parse_stdout_to_metrics(txt)
            # update labels
            self.var_btc_trades.set(str(metrics.get("BTCUSDT_trades", "-")))
            self.var_btc_cap.set(str(metrics.get("BTCUSDT_final_capital", "-")))
            self.var_eth_trades.set(str(metrics.get("ETHUSDT_trades", "-")))
            self.var_eth_cap.set(str(metrics.get("ETHUSDT_final_capital", "-")))
            # table
            for i in self.tv.get_children(): self.tv.delete(i)
            for name, val, sign in feats:
                self.tv.insert("", "end", values=(name, val, sign))

            # save metrics CSV
            if metrics or feats:
                with self.current_csv.open("w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(["metric","value"])
                    for k,v in metrics.items():
                        w.writerow([k, v])
                    if feats:
                        w.writerow([]); w.writerow(["feature","delta","sign"])
                        for name, val, sign in feats:
                            w.writerow([name, val, sign])
                self._append(f"\n[INFO] Saved metrics CSV: {self.current_csv}\n")
        except Exception as e:
            self._append(f"[WARN] parse/save failed: {e!r}\n")

        self.status.config(text="Finished")
        self.btn_stop.config(state="disabled"); self.btn_run.config(state="normal")

def main():
    root = tk.Tk()
    ControlCenter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
