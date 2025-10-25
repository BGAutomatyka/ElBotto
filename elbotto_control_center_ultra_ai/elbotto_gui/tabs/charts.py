import tkinter as tk
from tkinter import ttk, messagebox
class ChartsTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Charts")
        ttk.Label(self, text="Wykresy equity i ΔPnL po runie.").pack(padx=8, pady=8)
    def plot_equity(self, times, equity):
        try:
            import matplotlib.pyplot as plt
        except Exception:
            messagebox.showwarning("Charts","Matplotlib not available."); return
        if not equity: messagebox.showinfo("Charts","Brak equity."); return
        plt.figure(); plt.plot(times, equity); plt.title("Equity"); plt.xlabel("time"); plt.ylabel("equity"); plt.tight_layout(); plt.show()
    def plot_features(self, feats):
        try:
            import matplotlib.pyplot as plt
        except Exception:
            messagebox.showwarning("Charts","Matplotlib not available."); return
        if not feats: messagebox.showinfo("Charts","Brak cech."); return
        names=[f[0] for f in feats]; vals=[f[1] for f in feats]
        plt.figure(); plt.bar(names, vals); plt.xticks(rotation=60, ha="right"); plt.title("Feature ΔPnL"); plt.tight_layout(); plt.show()
