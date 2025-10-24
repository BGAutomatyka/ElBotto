
import tkinter as tk
from tkinter import ttk, filedialog

class TrainingTab(ttk.LabelFrame):
    def __init__(self, master, var_script, defaults_script="src\\elbotto\\ml\\train.py"):
        super().__init__(master, text="Training")
        self.var_script = var_script; self.var_script.set(defaults_script)
        self.var_epochs = tk.IntVar(value=50)
        self.var_lr     = tk.DoubleVar(value=1e-3)
        self.var_val    = tk.DoubleVar(value=0.2)

        ttk.Label(self, text="Train script:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_script, width=60).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Browse…", command=self._pick).grid(row=0, column=2, padx=6)

        ttk.Label(self, text="Epochs / LR / Val:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        fr = ttk.Frame(self); fr.grid(row=1, column=1, sticky="w")
        ttk.Entry(fr, textvariable=self.var_epochs, width=6).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left", padx=4)
        ttk.Entry(fr, textvariable=self.var_lr, width=10).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left", padx=4)
        ttk.Entry(fr, textvariable=self.var_val, width=6).pack(side="left")

    def _pick(self):
        p = filedialog.askopenfilename(title="Select Train script", filetypes=[("Python","*.py"),("All","*.*")])
        if p: self.var_script.set(p)
