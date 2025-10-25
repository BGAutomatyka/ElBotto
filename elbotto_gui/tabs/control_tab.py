import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import subprocess, os, json, threading, time

CREATE_NEW_CONSOLE = 0x00000010

def _read_json(p: Path):
    try:
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def _write_json_atomic(p: Path, data: dict):
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(p)

class ControlTab(ttk.LabelFrame):
    """
    Sterowanie całym stosem (Start/Stop) + runtime tuning:
    threshold / risk_per_trade / max_position -> results/runtime_overrides.json
    """
    def __init__(self, master):
        super().__init__(master, text="Control (LIVE / STOP)")
        # domyślne ścieżki
        self.var_bat  = tk.StringVar(value="ELBOTTO_ALL_IN_ONE_v2_1.bat")
        self.var_json = tk.StringVar(value="results\\runtime_overrides.json")
        # wartości regulowane
        self.var_thr    = tk.DoubleVar(value=0.10)
        self.var_risk   = tk.DoubleVar(value=0.005)
        self.var_maxpos = tk.IntVar(value=1)
        # auto-apply
        self.var_auto = tk.BooleanVar(value=True)
        # „podgląd” aktualnych wartości z pliku
        self.lbl_current = tk.StringVar(value="threshold=?, risk=?, max_position=?")

        self._build_ui()

        # pętla odświeżająca co 1 s
        self._running = True
        threading.Thread(target=self._loop, daemon=True).start()

    # ---------- UI ----------
    def _build_ui(self):
        r = 0
        ttk.Label(self, text="Runner (.bat):").grid(row=r, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_bat, width=44).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Browse…", command=self._pick_bat, width=12).grid(row=r, column=2, padx=6); r += 1

        ttk.Label(self, text="Overrides JSON:").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_json, width=44).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Open", command=self._open_json, width=12).grid(row=r, column=2, padx=6); r += 1

        # THRESHOLD
        ttk.Label(self, text="threshold").grid(row=r, column=0, sticky="e", padx=6)
        thr_scale = ttk.Scale(self, from_=0.0, to=0.50, variable=self.var_thr, command=lambda v: self._sync_spin(self.spin_thr, float(v)))
        thr_scale.grid(row=r, column=1, sticky="we", padx=6)
        self.spin_thr = ttk.Spinbox(self, from_=0.0, to=0.50, increment=0.005, textvariable=self.var_thr, width=10, command=self._maybe_apply)
        self.spin_thr.grid(row=r, column=2, padx=6); r += 1

        # RISK
        ttk.Label(self, text="risk_per_trade").grid(row=r, column=0, sticky="e", padx=6)
        risk_scale = ttk.Scale(self, from_=0.0, to=0.05, variable=self.var_risk, command=lambda v: self._sync_spin(self.spin_risk, float(v)))
        risk_scale.grid(row=r, column=1, sticky="we", padx=6)
        self.spin_risk = ttk.Spinbox(self, from_=0.0, to=0.05, increment=0.001, textvariable=self.var_risk, width=10, command=self._maybe_apply)
        self.spin_risk.grid(row=r, column=2, padx=6); r += 1

        # MAX POSITION
        ttk.Label(self, text="max_position").grid(row=r, column=0, sticky="e", padx=6)
        pos_scale = ttk.Scale(self, from_=0, to=5, variable=self.var_maxpos, command=lambda v: self._sync_spin(self.spin_pos, int(float(v))))
        pos_scale.grid(row=r, column=1, sticky="we", padx=6)
        self.spin_pos = ttk.Spinbox(self, from_=0, to=5, increment=1, textvariable=self.var_maxpos, width=10, command=self._maybe_apply)
        self.spin_pos.grid(row=r, column=2, padx=6); r += 1

        # przyciski
        ttk.Checkbutton(self, text="Auto-apply every 1s", variable=self.var_auto).grid(row=r, column=0, padx=6, pady=8, sticky="w")
        ttk.Button(self, text="Apply now", command=self.apply_now).grid(row=r, column=1, padx=6, pady=8, sticky="we")
        ttk.Button(self, text="Reset (clear file)", command=self.reset_file).grid(row=r, column=2, padx=6, pady=8, sticky="we"); r += 1

        # start/stop + log
        ttk.Button(self, text="▶ Start LIVE", command=self._start_live).grid(row=r, column=0, padx=6, p
