# gui_runner.py
# Prosty GUI do uruchamiania run_quickstart_tuned.py z parametrami.
# Działa na Windows bez dodatkowych bibliotek (Tkinter w standardzie).

import os
import sys
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "ElBotto – QuickStart GUI"

def find_venv_python() -> str:
    """Zwraca ścieżkę do Pythona z .venv jeżeli istnieje, inaczej aktualny interpreter."""
    here = Path(__file__).resolve().parent
    venv_py = here / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable  # fallback

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("840x640")
        self.minsize(820, 620)

        self.python_path = tk.StringVar(value=find_venv_python())
        self.dataset = tk.StringVar(value=str(Path("data/binance_order_book_small.csv")))
        self.threshold = tk.StringVar(value="0.50")
        self.capital = tk.StringVar(value="5000")
        self.max_position = tk.StringVar(value="1.0")
        self.fee = tk.StringVar(value="0.0002")
        self.windows = tk.StringVar(value="3 6 9")
        self.symbols = tk.StringVar(value="BTCUSDT ETHUSDT")

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}
        frm = ttk.Frame(self)
        frm.pack(fill="both", expand=True)

        # ścieżka do pythona (z .venv)
        row0 = ttk.Frame(frm); row0.pack(fill="x", **pad)
        ttk.Label(row0, text="Python (.venv):", width=18).pack(side="left")
        ttk.Entry(row0, textvariable=self.python_path).pack(side="left", fill="x", expand=True)
        ttk.Button(row0, text="Wyszukaj…", command=self.pick_python).pack(side="left", padx=6)

        # dataset
        row1 = ttk.Frame(frm); row1.pack(fill="x", **pad)
        ttk.Label(row1, text="Dataset (CSV):", width=18).pack(side="left")
        ttk.Entry(row1, textvariable=self.dataset).pack(side="left", fill="x", expand=True)
        ttk.Button(row1, text="Wybierz plik…", command=self.pick_dataset).pack(side="left", padx=6)

        # parametry
        grid = ttk.LabelFrame(frm, text="Parametry")
        grid.pack(fill="x", **pad)

        def add_row(parent, label, var, width=16, hint=""):
            r = ttk.Frame(parent); r.pack(fill="x", **pad)
            ttk.Label(r, text=label, width=18).pack(side="left")
            e = ttk.Entry(r, textvariable=var, width=width)
            e.pack(side="left")
            if hint:
                ttk.Label(r, text=hint, foreground="#666").pack(side="left", padx=10)
            return e

        add_row(grid, "threshold:", self.threshold, hint="np. 0.50")
        add_row(grid, "capital:", self.capital, hint="np. 5000")
        add_row(grid, "max-position:", self.max_position, hint="np. 1.0")
        add_row(grid, "fee:", self.fee, hint="np. 0.0002")
        add_row(grid, "windows:", self.windows, hint="np. 3 6 9 (spacje)")
        add_row(grid, "symbols:", self.symbols, hint="np. BTCUSDT ETHUSDT")

        # przyciski RUN / STOP
        btns = ttk.Frame(frm); btns.pack(fill="x", **pad)
        self.run_btn = ttk.Button(btns, text="▶ RUN", command=self.on_run)
        self.run_btn.pack(side="left")
        self.stop_btn = ttk.Button(btns, text="■ STOP", command=self.on_stop, state="disabled")
        self.stop_btn.pack(side="left", padx=8)

        # wyjście konsoli
        out_frame = ttk.LabelFrame(frm, text="Wyjście")
        out_frame.pack(fill="both", expand=True, **pad)
        self.text = tk.Text(out_frame, wrap="word", height=18)
        self.text.pack(fill="both", expand=True)
        self.text.insert("end", "Gotowy. Ustaw parametry i kliknij RUN.\n")

        # statusbar
        self.status = tk.StringVar(value="Iddle")
        sbar = ttk.Label(frm, textvariable=self.status, anchor="w")
        sbar.pack(fill="x", **pad)

        # proces
        self.proc = None
        self.reader_thread = None

    # Handlery
    def pick_python(self):
        p = filedialog.askopenfilename(title="Wskaż python.exe (.venv)",
                                       filetypes=[("python.exe", "python.exe"), ("Wszystkie", "*.*")])
        if p: self.python_path.set(p)

    def pick_dataset(self):
        p = filedialog.askopenfilename(title="Wybierz dataset CSV",
                                       filetypes=[("CSV", "*.csv"), ("Wszystkie", "*.*")],
                                       initialdir=str(Path.cwd()))
        if p: self.dataset.set(p)

    def append_out(self, txt: str):
        self.text.insert("end", txt)
        self.text.see("end")

    def build_cmd(self):
        # skrypt uruchamiany
        script = Path("run_quickstart_tuned.py")
        if not script.exists():
            messagebox.showerror(APP_TITLE, f"Nie znaleziono {script}. Umieść GUI w głównym folderze projektu.")
            return None

        # bez znaków '=' – Windows PowerShell
        cmd = [
            self.python_path.get(),
            str(script),
            "--dataset", self.dataset.get(),
            "--threshold", self.threshold.get(),
            "--capital", self.capital.get(),
            "--max-position", self.max_position.get(),
            "--fee", self.fee.get(),
        ]
        # windows (okna czasowe) – lista po spacji
        wins = self.windows.get().strip().split()
        if wins:
            cmd.append("--windows"); cmd.extend(wins)

        # symbols (jeśli Twój skrypt to obsługuje; jeśli nie, po prostu nie przeszkadza)
        syms = self.symbols.get().strip().split()
        if syms:
            cmd.append("--symbols"); cmd.extend(syms)

        return cmd

    def on_run(self):
        if self.proc and self.proc.poll() is None:
            messagebox.showinfo(APP_TITLE, "Proces już działa.")
            return

        cmd = self.build_cmd()
        if not cmd: return

        self.append_out(f"\n[CMD] {' '.join(cmd)}\n")
        self.status.set("Running…")
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")

        # uruchom w tle, czytaj stdout w wątku
        def worker():
            try:
                self.proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    cwd=str(Path(__file__).resolve().parent),
                    text=True,
                    bufsize=1
                )
                for line in self.proc.stdout:
                    self.append_out(line)
                rc = self.proc.wait()
                self.append_out(f"\n[EXIT] code={rc}\n")
            except Exception as e:
                self.append_out(f"\n[ERROR] {e}\n")
            finally:
                self.status.set("Done")
                self.run_btn.config(state="normal")
                self.stop_btn.config(state="disabled")
                self.proc = None

        self.reader_thread = threading.Thread(target=worker, daemon=True)
        self.reader_thread.start()
