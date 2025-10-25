import tkinter as tk
from tkinter import ttk, messagebox
import os, json, time
from pathlib import Path
from ..util.proc_manager import ProcManager

class SelfTestTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Diagnostics & Self-Test")
        self.pm = ProcManager()
        self.var_status = tk.StringVar(value="Ready")
        self._build()

    def _build(self):
        r=0
        # Env panel
        env = ttk.LabelFrame(self, text="Environment")
        env.grid(row=r, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)
        self.var_python = tk.StringVar(value=r".venv\Scripts\python.exe")
        ttk.Label(env, text="Python venv:").grid(row=0, column=0, sticky="e")
        ttk.Entry(env, textvariable=self.var_python, width=50).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Button(env, text="Check", command=self._check_env).grid(row=0, column=2, padx=6)
        env.grid_columnconfigure(1, weight=1)

        # Actions
        act = ttk.LabelFrame(self, text="Quick Tests")
        act.grid(row=r+1, column=0, sticky="nsew", padx=6, pady=6)
        ttk.Button(act, text="1) Generate Toy LOB", command=self._toy).grid(row=0, column=0, sticky="w", padx=6, pady=3)
        ttk.Button(act, text="2) Featurize OB", command=self._featurize).grid(row=1, column=0, sticky="w", padx=6, pady=3)
        ttk.Button(act, text="3) Regime", command=self._regime).grid(row=2, column=0, sticky="w", padx=6, pady=3)
        ttk.Button(act, text="4) WFV (fast)", command=self._wfv_fast).grid(row=3, column=0, sticky="w", padx=6, pady=3)
        ttk.Button(act, text="5) Heatmap", command=self._heatmap).grid(row=4, column=0, sticky="w", padx=6, pady=3)
        ttk.Button(act, text="Run ALL (1→5)", command=self._all).grid(row=5, column=0, sticky="w", padx=6, pady=8)
        ttk.Button(act, text="Kill All", command=self._kill).grid(row=5, column=1, sticky="w", padx=6, pady=8)

        # Output viewer
        out = ttk.LabelFrame(self, text="Output")
        out.grid(row=r+1, column=1, sticky="nsew", padx=6, pady=6)
        self.txt = tk.Text(out, height=22, wrap="word"); self.txt.pack(fill="both", expand=True, padx=6, pady=6)

        # Status bar
        ttk.Label(self, textvariable=self.var_status).grid(row=r+2, column=0, columnspan=2, sticky="we", padx=6, pady=6)

        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(r+1, weight=1)

    def _log(self, s): self.txt.insert("end", s + "\n"); self.txt.see("end")
    def _py(self): return self.var_python.get()

    def _check_env(self):
        p = Path(self._py())
        ok = p.exists()
        self._log(f"[ENV] venv python exists: {ok} -> {p}")
        if not ok:
            self._log("[ENV] Missing .venv. Create venv and install dependencies.")
        else:
            # quick python diag
            cmd = f"{self._py()} tools/diag_env.py"
            info = self.pm.start(cmd)
            self.after(300, lambda: self._drain(info))

    def _toy(self):
        cmd = f"{self._py()} smoke_test/make_toy_lob.py"
        info = self.pm.start(cmd); self._log(f"[RUN] {cmd}")
        self.after(300, lambda: self._drain(info))

    def _featurize(self):
        cmd = f"{self._py()} -m elbotto_ob.ob.featurizer --in data/toy_lob.csv --out results/lob_features.csv --levels 3 --agg-sec 1"
        info = self.pm.start(cmd); self._log(f"[RUN] {cmd}")
        self.after(300, lambda: self._drain(info))

    def _regime(self):
        cmd = f"{self._py()} -m elbotto_ob.regime.online --in results/lob_features.csv --out results/regime_state.json"
        info = self.pm.start(cmd); self._log(f"[RUN] {cmd}")
        self.after(300, lambda: self._drain(info))

    def _wfv_fast(self):
        cmd = f"{self._py()} -m elbotto_patch.wfv.walk_forward --csv results/lob_features.csv --mode microprice --thresholds 0.05,0.10 --train-rows 20000 --test-rows 5000 --step-rows 5000 --fee-bps 2 --latency-ms 50 --out-prefix results/wfv"
        info = self.pm.start(cmd); self._log(f"[RUN] {cmd}")
        self.after(300, lambda: self._drain(info))

    def _heatmap(self):
        cmd = f"{self._py()} -m elbotto_patch.viz.ob_heatmap --csv results/lob_features.csv --levels 3 --out results/ob_heatmap.png"
        info = self.pm.start(cmd); self._log(f"[RUN] {cmd}")
        self.after(300, lambda: self._drain(info))

    def _all(self):
        self._toy(); self.after(800, self._featurize); self.after(1600, self._regime); self.after(2400, self._wfv_fast); self.after(3200, self._heatmap)

    def _kill(self):
        self.pm.kill_all(); self._log("[KILL] sent terminate to all subprocesses")

    def _drain(self, info):
        if info.rc is None:
            # still running
            if info.output:
                for ln in info.output[-10:]:
                    self._log(ln)
            self.after(500, lambda: self._drain(info))
        else:
            self._log(f"[EXIT] rc={info.rc}")
            if info.output:
                for ln in info.output[-20:]:
                    self._log(ln)
