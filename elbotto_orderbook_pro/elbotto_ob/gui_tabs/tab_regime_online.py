import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, shlex

class RegimeOnlineTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Regime Online")
        self.var_in = tk.StringVar(value="results\\lob_features.csv")
        self.var_out = tk.StringVar(value="results\\regime_state.json")
        ttk.Label(self, text="Features CSV:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_in, width=60).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Button(self, text="...", command=self._pick_in).grid(row=0, column=2, padx=4)
        ttk.Label(self, text="Out JSON:").grid(row=1, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_out, width=60).grid(row=1, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Run", command=self._run).grid(row=1, column=2, padx=4)
        self.grid_columnconfigure(1, weight=1)
    def _pick_in(self):
        p = filedialog.askopenfilename(title="Features CSV", filetypes=[("CSV","*.csv"),("All","*.*")])
        if p: self.var_in.set(p)
    def _run(self):
        cmd = f".venv\\Scripts\\python.exe -m elbotto_ob.regime.online --in {self.var_in.get()} --out {self.var_out.get()}"
        try:
            subprocess.Popen(shlex.split(cmd))
            messagebox.showinfo("Regime", "Regime detector started.")
        except Exception as e:
            messagebox.showerror("Regime", repr(e))
