
import tkinter as tk
from tkinter import ttk
from ..indicators import INDICATORS
from ..storage import save_indicators, load_indicators

class IndicatorWindow(tk.Toplevel):
    def __init__(self, master, on_change=None):
        super().__init__(master)
        self.title("Indicators")
        self.geometry("520x640")
        self.on_change = on_change
        self.vars = {}
        self.filtered = list(INDICATORS)
        self._build_ui()
        self._load_selected()

    def _build_ui(self):
        top = ttk.Frame(self); top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Search:").pack(side="left")
        self.var_q = tk.StringVar()
        ent = ttk.Entry(top, textvariable=self.var_q, width=30); ent.pack(side="left", padx=6)
        ent.bind("<KeyRelease>", lambda e: self._apply_filter())
        ttk.Button(top, text="Select all", command=self._select_all).pack(side="left", padx=4)
        ttk.Button(top, text="None", command=self._select_none).pack(side="left", padx=4)

        self.canvas = tk.Canvas(self); self.canvas.pack(fill="both", expand=True)
        self.frm = ttk.Frame(self.canvas)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scroll.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.canvas.create_window((0,0), window=self.frm, anchor="nw")
        self.frm.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self._render_checks()

        bottom = ttk.Frame(self); bottom.pack(fill="x", padx=8, pady=8)
        self.var_append = tk.BooleanVar(value=False)
        ttk.Checkbutton(bottom, text="Append '--indicators ...' to args on Run", variable=self.var_append).pack(side="left")
        ttk.Button(bottom, text="Save", command=self._save).pack(side="right", padx=6)

    def _render_checks(self):
        for w in self.frm.winfo_children():
            w.destroy()
        self.vars.clear()
        for i, name in enumerate(self.filtered):
            v = tk.BooleanVar(value=False)
            chk = ttk.Checkbutton(self.frm, text=name, variable=v)
            chk.grid(row=i, column=0, sticky="w", padx=6, pady=2)
            self.vars[name] = v

    def _apply_filter(self):
        q = self.var_q.get().strip().lower()
        if not q:
            self.filtered = list(INDICATORS)
        else:
            self.filtered = [n for n in INDICATORS if q in n.lower()]
        self._render_checks()
        self._restore_selected()

    def _select_all(self):
        for v in self.vars.values(): v.set(True)

    def _select_none(self):
        for v in self.vars.values(): v.set(False)

    def _save(self):
        selected = [name for name, v in self.vars.items() if v.get()]
        save_indicators(selected)
        if self.on_change: self.on_change(selected, self.var_append.get())
        self.destroy()

    def _load_selected(self):
        sel = set(load_indicators())
        self._restore_selected(sel)

    def _restore_selected(self, sel=None):
        if sel is None:
            sel = set(load_indicators())
        for name, v in self.vars.items():
            v.set(name in sel)
