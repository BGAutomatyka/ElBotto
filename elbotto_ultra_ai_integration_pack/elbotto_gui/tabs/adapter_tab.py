import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, shlex, json, os, time, threading
from pathlib import Path

class AdapterPlusTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Adapter+ (News + Regime + Rules)")
        self.var_results = tk.StringVar(value="results")
        self.var_rules = tk.StringVar(value="rules.json")
        self.var_interval = tk.IntVar(value=5)
        self.proc = None

        r=0
        ttk.Label(self, text="results/ dir:").grid(row=r, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_results, width=50).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self, text="...", command=self._pick_results).grid(row=r, column=2, padx=4); r+=1

        ttk.Label(self, text="Rules JSON:").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_rules, width=50).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Browse", command=self._pick_rules).grid(row=r, column=2, padx=4); r+=1

        ttk.Label(self, text="Interval (s):").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_interval, width=8).grid(row=r, column=1, sticky="w", padx=6)

        ttk.Button(self, text="Start", command=self._start).grid(row=r, column=2, padx=4)
        ttk.Button(self, text="Stop", command=self._stop).grid(row=r, column=3, padx=4); r+=1

        self.tv = ttk.Treeview(self, columns=("k","v"), show="headings", height=8)
        self.tv.heading("k", text="key"); self.tv.heading("v", text="value")
        self.tv.grid(row=r, column=0, columnspan=4, sticky="nsew", padx=6, pady=6)
        self.grid_columnconfigure(1, weight=1); self.grid_rowconfigure(r, weight=1)
        self.after(1000, self._tick)

    def _pick_results(self):
        p = filedialog.askdirectory(title="Pick results directory")
        if p: self.var_results.set(p)
    def _pick_rules(self):
        p = filedialog.askopenfilename(title="Rules JSON", filetypes=[("JSON","*.json"),("All","*.*")])
        if p: self.var_rules.set(p)

    def _start(self):
        if self.proc and self.proc.poll() is None:
            messagebox.showinfo("Adapter+","Already running"); return
        cmd = f".venv\\Scripts\\python.exe -m elbotto_patch.adapter.elbotto_runtime_adapter_plus --results {self.var_results.get()} --interval {self.var_interval.get()} --rules {self.var_rules.get()}"
        try:
            self.proc = subprocess.Popen(shlex.split(cmd))
            messagebox.showinfo("Adapter+","Started.")
        except Exception as e:
            messagebox.showerror("Adapter+", repr(e))

    def _stop(self):
        try:
            if self.proc and self.proc.poll() is None:
                self.proc.terminate()
                messagebox.showinfo("Adapter+","Stopped.")
        except Exception:
            pass

    def _tick(self):
        try:
            path = Path(self.var_results.get()) / "runtime_overrides.json"
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                for i in self.tv.get_children(): self.tv.delete(i)
                for k,v in data.items():
                    self.tv.insert("", "end", values=(k, str(v)))
        except Exception:
            pass
        self.after(1000, self._tick)
