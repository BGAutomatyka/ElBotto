import tkinter as tk
from tkinter import ttk
class MetricsPanel(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.var_btc_trades = tk.StringVar(value="-"); self.var_btc_cap = tk.StringVar(value="-")
        self.var_eth_trades = tk.StringVar(value="-"); self.var_eth_cap = tk.StringVar(value="-")
        g = ttk.Frame(self); g.pack(fill="x", padx=6, pady=6)
        ttk.Label(g, text="BTC trades:").grid(row=0, column=0, sticky="w"); ttk.Label(g, textvariable=self.var_btc_trades).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Label(g, text="BTC capital:").grid(row=0, column=2, sticky="w"); ttk.Label(g, textvariable=self.var_btc_cap).grid(row=0, column=3, sticky="w", padx=6)
        ttk.Label(g, text="ETH trades:").grid(row=1, column=0, sticky="w"); ttk.Label(g, textvariable=self.var_eth_trades).grid(row=1, column=1, sticky="w", padx=6)
        ttk.Label(g, text="ETH capital:").grid(row=1, column=2, sticky="w"); ttk.Label(g, textvariable=self.var_eth_cap).grid(row=1, column=3, sticky="w", padx=6)
        self.tv = ttk.Treeview(self, columns=("feature","delta","sign"), show="headings", height=10)
        for c in ("feature","delta","sign"): self.tv.heading(c, text=c); self.tv.column(c, width=150 if c=="feature" else 70)
        self.tv.pack(fill="both", expand=True, padx=6, pady=6)
    def update_metrics(self, m: dict):
        if "BTCUSDT_trades" in m: self.var_btc_trades.set(str(m["BTCUSDT_trades"]))
        if "BTCUSDT_cap" in m:    self.var_btc_cap.set(str(m["BTCUSDT_cap"]))
        if "ETHUSDT_trades" in m: self.var_eth_trades.set(str(m["ETHUSDT_trades"]))
        if "ETHUSDT_cap" in m:    self.var_eth_cap.set(str(m["ETHUSDT_cap"]))
    def set_features(self, feats):
        for i in self.tv.get_children(): self.tv.delete(i)
        for name, val, sign in feats: self.tv.insert("", "end", values=(name, val, sign))
