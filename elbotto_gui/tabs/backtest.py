
import tkinter as tk
from tkinter import ttk, filedialog

class BacktestTab(ttk.LabelFrame):
    def __init__(self, master, var_script, defaults_script="src\\elbotto\\backtest\\backtest.py"):
        super().__init__(master, text="Backtest")
        self.var_script = var_script
        self.var_script.set(defaults_script)
        ttk.Label(self, text="Script:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_script, width=60).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Browse…", command=self._pick).grid(row=0, column=2, padx=6)

    def _pick(self):
        p = filedialog.askopenfilename(title="Select Backtest script", filetypes=[("Python","*.py"),("All","*.*")])
        if p: self.var_script.set(p)
