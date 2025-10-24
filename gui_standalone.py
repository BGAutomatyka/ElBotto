import tkinter as tk
from tkinter import ttk
from pathlib import Path
import json, time, threading

def load_overrides(p=Path("results/runtime_overrides.json")):
    try: return json.loads(p.read_text(encoding="utf-8"))
    except: return {}

def save_overrides(d, p=Path("results/runtime_overrides.json")):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, indent=2), encoding="utf-8")

class App(ttk.Frame):
    def __init__(self, master):
        super().__init__(master); self.pack(fill="both", expand=True, padx=8, pady=8)
        self.thr=tk.DoubleVar(value=0.10); self.risk=tk.DoubleVar(value=0.005); self.maxp=tk.IntVar(value=1)
        self.lbl=tk.StringVar(value="current: (no file)")
        f=ttk.LabelFrame(self,text="Overrides"); f.pack(fill="x")
        ttk.Label(f,text="threshold").grid(row=0,column=0,sticky="e"); ttk.Entry(f,textvariable=self.thr,width=10).grid(row=0,column=1)
        ttk.Label(f,text="risk_per_trade").grid(row=0,column=2,sticky="e"); ttk.Entry(f,textvariable=self.risk,width=10).grid(row=0,column=3)
        ttk.Label(f,text="max_position").grid(row=0,column=4,sticky="e"); ttk.Entry(f,textvariable=self.maxp,width=10).grid(row=0,column=5)
        ttk.Button(f,text="Apply",command=self.apply).grid(row=0,column=6,padx=6)
        ttk.Label(self,textvariable=self.lbl).pack(fill="x", pady=6)
        threading.Thread(target=self._loop,daemon=True).start()
    def apply(self):
        d={"threshold":float(self.thr.get()),"risk_per_trade":float(self.risk.get()),"max_position":int(self.maxp.get())}
        save_overrides(d); self._update()
    def _update(self):
        d=load_overrides()
        self.lbl.set(f"current: threshold={d.get('threshold')}, risk={d.get('risk_per_trade')}, max_position={d.get('max_position')}")
    def _loop(self):
        while True:
            self._update(); time.sleep(1.0)

def main():
    root=tk.Tk(); root.title("ElBotto GUI"); root.geometry("520x160"); App(root); root.mainloop()
if __name__=="__main__": main()
