import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, shlex

class OrderBookTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Order Book Featurizer")
        self.var_in = tk.StringVar(value="data\\lob.csv")
        self.var_out = tk.StringVar(value="results\\lob_features.csv")
        self.var_levels = tk.IntVar(value=10)
        self.var_agg = tk.IntVar(value=1)
        r=0
        ttk.Label(self, text="LOB CSV:").grid(row=r, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_in, width=60).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self, text="...", command=self._pick_in).grid(row=r, column=2, padx=4); r+=1
        ttk.Label(self, text="Features CSV:").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_out, width=60).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Browse", command=self._pick_out).grid(row=r, column=2, padx=4); r+=1
        ttk.Label(self, text="Levels / Agg-sec:").grid(row=r, column=0, sticky="e", padx=6)
        fr=ttk.Frame(self); fr.grid(row=r, column=1, sticky="w")
        ttk.Entry(fr, textvariable=self.var_levels, width=6).pack(side="left")
        ttk.Entry(fr, textvariable=self.var_agg, width=6).pack(side="left", padx=8)
        ttk.Button(self, text="Run", command=self._run).grid(row=r, column=2, padx=4); r+=1
        self.grid_columnconfigure(1, weight=1)
    def _pick_in(self):
        p = filedialog.askopenfilename(title="LOB CSV", filetypes=[("CSV","*.csv"),("All","*.*")])
        if p: self.var_in.set(p)
    def _pick_out(self):
        p = filedialog.asksaveasfilename(title="Features CSV", defaultextension=".csv")
        if p: self.var_out.set(p)
    def _run(self):
        cmd = f".venv\\Scripts\\python.exe -m elbotto_ob.ob.featurizer --in {self.var_in.get()} --out {self.var_out.get()} --levels {self.var_levels.get()} --agg-sec {self.var_agg.get()}"
        try:
            subprocess.Popen(shlex.split(cmd))
            messagebox.showinfo("OB", "Featurizer started.")
        except Exception as e:
            messagebox.showerror("OB", repr(e))
