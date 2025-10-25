
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

class ChartsTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Charts (features/ΔPnL)")
        ttk.Label(self, text="Ten moduł używa matplotlib (opcjonalnie). Po zakończeniu runa spróbuj narysować wykres ΔPnL cech.").pack(padx=8, pady=8)

    def plot_features(self, feats):
        try:
            import matplotlib
            import matplotlib.pyplot as plt
        except Exception:
            messagebox.showwarning("Charts", "Matplotlib not available in this environment.")
            return
        if not feats:
            messagebox.showinfo("Charts", "Brak danych cech do wykresu.")
            return
        names = [f[0] for f in feats]
        vals  = [f[1] for f in feats]
        plt.figure()
        plt.bar(names, vals)
        plt.xticks(rotation=60, ha="right")
        plt.title("Feature ΔPnL")
        plt.tight_layout()
        plt.show()
