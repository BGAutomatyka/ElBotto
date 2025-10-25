import tkinter as tk
from tkinter import ttk, messagebox
from ..news.engine import NewsEngine
from pathlib import Path

class NewsAITab(ttk.LabelFrame):
    def __init__(self, master, results_dir: Path):
        super().__init__(master, text="News AI (auto/manual)")
        self.results_dir = results_dir
        self.engine = NewsEngine(results_dir)
        self.var_interval = tk.IntVar(value=90)
        self.var_include = tk.StringVar(value="bitcoin, ethereum, etf, hack, cpi, fomc")
        self.var_exclude = tk.StringVar(value="rumor, meme")
        self.var_rss = tk.StringVar(value="https://news.google.com/rss/search?q=bitcoin&hl=en-US&gl=US&ceid=US:en")
        self.var_csv = tk.StringVar(value="")  # optional local backfill
        self.var_news_weight = tk.DoubleVar(value=0.6)

        r=0
        ttk.Label(self, text="RSS URL:").grid(row=r, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_rss, width=70).grid(row=r, column=1, sticky="we", padx=6)
        r+=1
        ttk.Label(self, text="Include / Exclude:").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_include, width=35).grid(row=r, column=1, sticky="w", padx=4)
        ttk.Entry(self, textvariable=self.var_exclude, width=20).grid(row=r, column=1, sticky="e", padx=4)
        r+=1
        ttk.Label(self, text="Poll every (s):").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_interval, width=8).grid(row=r, column=1, sticky="w", padx=6)
        ttk.Label(self, text="News weight:").grid(row=r, column=1, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_news_weight, width=8).grid(row=r, column=1, sticky="e", padx=6, ipadx=30)
        r+=1
        ttk.Label(self, text="Local CSV (optional):").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_csv, width=70).grid(row=r, column=1, sticky="we", padx=6)
        r+=1
        self.btn_start = ttk.Button(self, text="Start feed", command=self._start); self.btn_start.grid(row=r, column=0, padx=6, pady=6)
        self.btn_stop  = ttk.Button(self, text="Stop", command=self._stop, state="disabled"); self.btn_stop.grid(row=r, column=1, sticky="w", padx=6, pady=6)

        self.tv = ttk.Treeview(self, columns=("ts","title","sent","syms"), show="headings", height=8)
        for c in ("ts","title","sent","syms"): self.tv.heading(c, text=c)
        self.tv.grid(row=r+1, column=0, columnspan=2, sticky="nsew", padx=6, pady=6)
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(r+1, weight=1)

    def _start(self):
        include = [w.strip() for w in self.var_include.get().split(",") if w.strip()]
        exclude = [w.strip() for w in self.var_exclude.get().split(",") if w.strip()]
        if self.var_rss.get().strip():
            self.engine.add_source({"type":"rss","url":self.var_rss.get().strip(),"include":include,"exclude":exclude,"symbols":["BTCUSDT","ETHUSDT"]})
        if self.var_csv.get().strip():
            self.engine.add_source({"type":"csv","path":self.var_csv.get().strip(),"symbols":["BTCUSDT","ETHUSDT"]})
        self.engine.start(interval_sec=int(self.var_interval.get()))
        self.btn_start.config(state="disabled"); self.btn_stop.config(state="normal")
        self.after(200, self._drain)

    def _stop(self):
        self.engine.stop()
        self.btn_stop.config(state="disabled"); self.btn_start.config(state="normal")

    def _drain(self):
        changed = False
        while not self.engine.queue.empty():
            it = self.engine.queue.get()
            if it.get("type") in ("rss","csv"):
                self.tv.insert("", "end", values=(it.get("ts",""), it.get("title","")[:120], round(it.get("sentiment",0.0),3), " ".join(it.get("symbols",[]))))
                changed = True
        if self.engine.running: self.after(500, self._drain)

    def get_symbol_sentiment(self, sym: str) -> float:
        return self.engine.get_symbol_sentiment(sym)
