
import tkinter as tk
from tkinter import ttk

class MetricsPanel(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.var_btc_trades = tk.StringVar(value="-")
        self.var_btc_cap = tk.StringVar(value="-")
        self.var_eth_trades = tk.StringVar(value="-")
        self.var_eth_cap = tk.StringVar(value="-")

        g = ttk.Frame(self)
        g.pack(fill="x", padx=6, pady=6)
        ttk.Label(g, text="BTC trades:").grid(row=0, column=0, sticky="w"); ttk.Label(g, textvariable=self.var_btc_trades).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(g, text="BTC capital:").grid(row=0, column=2, sticky="w"); ttk.Label(g, textvariable=self.var_btc_cap).grid(row=0, column=3, sticky="w", padx=6)
        ttk.Label(g, text="ETH trades:").grid(row=1, column=0, sticky="w"); ttk.Label(g, textvariable=self.var_eth_trades).grid(row=1, column=1, sticky="w", padx=6)
        ttk.Label(g, text="ETH capital:").grid(row=1, column=2, sticky="w"); ttk.Label(g, textvariable=self.var_eth_cap).grid(row=1, column=3, sticky="w", padx=6)

        self.tv = ttk.Treeview(self, columns=("feature","delta","sign"), show="headings", height=8)
        self.tv.heading("feature", text="Feature")
        self.tv.heading("delta", text="ΔPnL")
        self.tv.heading("sign", text="+/-")
        self.tv.pack(fill="both", expand=True, padx=6, pady=6)

    def update_metrics(self, metrics: dict):
        if "BTCUSDT_trades" in metrics: self.var_btc_trades.set(str(metrics["BTCUSDT_trades"]))
        if "BTCUSDT_cap" in metrics: self.var_btc_cap.set(str(metrics["BTCUSDT_cap"]))
        if "ETHUSDT_trades" in metrics: self.var_eth_trades.set(str(metrics["ETHUSDT_trades"]))
        if "ETHUSDT_cap" in metrics: self.var_eth_cap.set(str(metrics["ETHUSDT_cap"]))

    def set_features(self, feats):
        # feats: list of (name, val, sign)
        for i in self.tv.get_children(): self.tv.delete(i)
        for name, val, sign in feats:
            self.tv.insert("", "end", values=(name, val, sign))
