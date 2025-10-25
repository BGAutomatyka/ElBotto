
import tkinter as tk
from tkinter import ttk

class SweepTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Batch Sweep (threshold)")
        self.var_start = tk.DoubleVar(value=0.30)
        self.var_stop  = tk.DoubleVar(value=0.65)
        self.var_step  = tk.DoubleVar(value=0.05)

        ttk.Label(self, text="Start / Stop / Step:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        fr = ttk.Frame(self); fr.grid(row=0, column=1, sticky="w")
        ttk.Entry(fr, textvariable=self.var_start, width=8).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left")
        ttk.Entry(fr, textvariable=self.var_stop, width=8).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left")
        ttk.Entry(fr, textvariable=self.var_step, width=8).pack(side="left")
