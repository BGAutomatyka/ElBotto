import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, shlex, os, sys

class WFVTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Walk-Forward Validation")
        self.var_csv = tk.StringVar(value="results\\lob_features.csv")
        self.var_thresholds = tk.StringVar(value="0.05,0.10,0.15,0.20")
        self.var_train = tk.IntVar(value=200000)
        self.var_test = tk.IntVar(value=50000)
        self.var_step = tk.IntVar(value=50000)
        self.var_fee = tk.DoubleVar(value=2.0)
        self.var_latency = tk.IntVar(value=50)
        self.var_mode = tk.StringVar(value="microprice")
        self.var_outprefix = tk.StringVar(value="results\\wfv")

        r=0
        ttk.Label(self, text="CSV:").grid(row=r, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_csv, width=70).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self, text="...", command=self._pick_csv).grid(row=r, column=2, padx=4); r+=1

        ttk.Label(self, text="Thresholds:").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_thresholds, width=25).grid(row=r, column=1, sticky="w", padx=6)
        ttk.Label(self, text="Mode:").grid(row=r, column=2, sticky="e")
        ttk.Combobox(self, textvariable=self.var_mode, values=["microprice","signal"], width=12, state="readonly").grid(row=r, column=3, sticky="w"); r+=1

        ttk.Label(self, text="Train/Test/Step (rows):").grid(row=r, column=0, sticky="e", padx=6)
        fr = ttk.Frame(self); fr.grid(row=r, column=1, sticky="w")
        ttk.Entry(fr, textvariable=self.var_train, width=10).pack(side="left")
        ttk.Entry(fr, textvariable=self.var_test, width=10).pack(side="left", padx=6)
        ttk.Entry(fr, textvariable=self.var_step, width=10).pack(side="left"); r+=1

        ttk.Label(self, text="Fee (bps) / Latency (ms):").grid(row=r, column=0, sticky="e", padx=6)
        fr2 = ttk.Frame(self); fr2.grid(row=r, column=1, sticky="w")
        ttk.Entry(fr2, textvariable=self.var_fee, width=10).pack(side="left")
        ttk.Entry(fr2, textvariable=self.var_latency, width=10).pack(side="left", padx=6)
        ttk.Label(self, text="Out prefix:").grid(row=r, column=2, sticky="e")
        ttk.Entry(self, textvariable=self.var_outprefix, width=18).grid(row=r, column=3, sticky="w"); r+=1

        ttk.Button(self, text="Run WFV", command=self._run).grid(row=r, column=0, padx=6, pady=8)
        ttk.Button(self, text="Open results folder", command=self._open_results).grid(row=r, column=1, sticky="w", padx=6, pady=8)
        self.grid_columnconfigure(1, weight=1)

    def _pick_csv(self):
        p = filedialog.askopenfilename(title="Features CSV", filetypes=[("CSV","*.csv"),("All","*.*")])
        if p: self.var_csv.set(p)

    def _open_results(self):
        try:
            os.startfile("results")
        except Exception:
            messagebox.showinfo("WFV","results folder not found.")

    def _run(self):
        cmd = (
            f".venv\\Scripts\\python.exe -m elbotto_patch.wfv.walk_forward "
            f"--csv {self.var_csv.get()} --mode {self.var_mode.get()} "
            f"--thresholds {self.var_thresholds.get()} --train-rows {self.var_train.get()} "
            f"--test-rows {self.var_test.get()} --step-rows {self.var_step.get()} "
            f"--fee-bps {self.var_fee.get()} --latency-ms {self.var_latency.get()} "
            f"--out-prefix {self.var_outprefix.get()}"
        )
        try:
            subprocess.Popen(shlex.split(cmd))
            messagebox.showinfo("WFV","Started. Wyniki trafią do results/…")
        except Exception as e:
            messagebox.showerror("WFV", repr(e))
