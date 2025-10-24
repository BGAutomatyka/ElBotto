import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import json

TEMPLATE = {
    "rules":[
        {"name":"Hack panic cut","symbols":["BTCUSDT","ETHUSDT"],"include_any":["hack","breach","exploit"],"include_all":[],"exclude_any":["rumor"],"min_sent":-0.2,"action":{"risk_mult":0.5,"threshold_delta":0.05,"pause_sec":120},"ttl_sec":600}
    ]
}

class RulesEditorTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Rules Editor")
        self.var_path = tk.StringVar(value="rules.json")
        ttk.Label(self, text="Rules file:").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_path, width=60).grid(row=0, column=1, sticky="we", padx=6)
        ttk.Button(self, text="...", command=self._pick).grid(row=0, column=2, padx=4)
        ttk.Button(self, text="New (template)", command=self._new).grid(row=0, column=3, padx=4)

        self.txt = tk.Text(self, wrap="none", height=20)
        self.txt.grid(row=1, column=0, columnspan=4, sticky="nsew", padx=6, pady=6)

        bar = ttk.Frame(self); bar.grid(row=2, column=0, columnspan=4, sticky="we", padx=6, pady=6)
        ttk.Button(bar, text="Load", command=self._load).pack(side="left")
        ttk.Button(bar, text="Save", command=self._save).pack(side="left", padx=6)
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(1, weight=1)

    def _pick(self):
        p = filedialog.asksaveasfilename(title="Rules JSON", defaultextension=".json")
        if p: self.var_path.set(p)
    def _new(self):
        self.txt.delete("1.0","end")
        self.txt.insert("1.0", json.dumps(TEMPLATE, indent=2))
    def _load(self):
        p = Path(self.var_path.get())
        if not p.exists():
            messagebox.showwarning("Rules","File not found."); return
        self.txt.delete("1.0","end")
        self.txt.insert("1.0", p.read_text(encoding="utf-8"))
    def _save(self):
        p = Path(self.var_path.get()); p.write_text(self.txt.get("1.0","end"), encoding="utf-8")
        messagebox.showinfo("Rules","Saved.")
