import tkinter as tk
from tkinter import ttk
from pathlib import Path
import threading, time

class MetricsTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Live Metrics")
        self.var_equity_csv = tk.StringVar(value="results\\equity_paper.csv")
        self.var_features_csv = tk.StringVar(value="results\\lob_features_live.csv")
        self._build()
        self._running = True
        self._start_refresher()

    def _build(self):
        r=0
        ttk.Label(self, text="Equity CSV:").grid(row=r, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_equity_csv, width=50).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Label(self, text="Features CSV:").grid(row=r, column=2, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_features_csv, width=40).grid(row=r, column=3, sticky="we", padx=6); r+=1

        try:
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            self.fig_eq = Figure(figsize=(6,2.3)); self.ax_eq = self.fig_eq.add_subplot(111)
            self.fig_sig = Figure(figsize=(6,2.3)); self.ax_sig = self.fig_sig.add_subplot(111)
            self.fig_pos = Figure(figsize=(6,2.3)); self.ax_pos = self.fig_pos.add_subplot(111)

            self.canvas_eq = FigureCanvasTkAgg(self.fig_eq, master=self); self.canvas_eq.get_tk_widget().grid(row=r, column=0, columnspan=4, sticky="nsew", padx=6, pady=6); r+=1
            self.canvas_sig = FigureCanvasTkAgg(self.fig_sig, master=self); self.canvas_sig.get_tk_widget().grid(row=r, column=0, columnspan=4, sticky="nsew", padx=6, pady=6); r+=1
            self.canvas_pos = FigureCanvasTkAgg(self.fig_pos, master=self); self.canvas_pos.get_tk_widget().grid(row=r, column=0, columnspan=4, sticky="nsew", padx=6, pady=6); r+=1
            self.grid_rowconfigure(r-1, weight=1)
        except Exception as e:
            ttk.Label(self, text=f"Matplotlib not available: {e}").grid(row=r, column=0, columnspan=4, sticky="we", padx=6, pady=6)

        self.grid_columnconfigure(1, weight=1); self.grid_columnconfigure(3, weight=1)

    def _start_refresher(self):
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def _loop(self):
        import pandas as pd
        while self._running:
            try:
                eqp = Path(self.var_equity_csv.get())
                if eqp.exists():
                    df = pd.read_csv(eqp)
                    if not df.empty:
                        self.ax_eq.clear(); self.ax_eq.plot(df["equity"].values); self.ax_eq.set_title("Equity"); self.ax_eq.grid(True)
                        self.ax_pos.clear(); self.ax_pos.plot(df["pos"].values); self.ax_pos.set_title("Position"); self.ax_pos.grid(True)
                        self.canvas_eq.draw(); self.canvas_pos.draw()
                fcp = Path(self.var_features_csv.get())
                if fcp.exists():
                    df2 = pd.read_csv(fcp)
                    if not df2.empty:
                        n = min(1000, len(df2))
                        sig = df2["microprice_imb"].values[-n:]
                        self.ax_sig.clear(); self.ax_sig.plot(sig); self.ax_sig.set_title("Signal (microprice_imb)"); self.ax_sig.grid(True)
                        self.canvas_sig.draw()
            except Exception:
                pass
            time.sleep(1.0)

    def destroy(self):
        self._running = False
        super().destroy()
