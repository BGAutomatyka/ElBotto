
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import csv, tempfile, os

class DataSweepTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Data Sweep (many CSVs / chunking)")
        self.var_folder = tk.StringVar(value="data")
        self.var_pattern = tk.StringVar(value="*.csv")
        self.var_chunk_rows = tk.IntVar(value=0)  # 0 = no chunking
        self.var_overlap = tk.IntVar(value=0)

        r=0
        ttk.Label(self, text="Folder:").grid(row=r, column=0, sticky="w", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_folder, width=50).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Browse…", command=self._pick_folder).grid(row=r, column=2, padx=6)
        r+=1
        ttk.Label(self, text="Pattern:").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(self, textvariable=self.var_pattern, width=20).grid(row=r, column=1, sticky="w", padx=6)
        r+=1
        ttk.Label(self, text="Chunk rows (0 = off):").grid(row=r, column=0, sticky="w", padx=6)
        ttk.Entry(self, textvariable=self.var_chunk_rows, width=10).grid(row=r, column=1, sticky="w", padx=6)
        ttk.Label(self, text="Overlap rows:").grid(row=r, column=2, sticky="w", padx=6)
        ttk.Entry(self, textvariable=self.var_overlap, width=10).grid(row=r, column=3, sticky="w", padx=6)

        for c in range(4): self.grid_columnconfigure(c, weight=1)

    def _pick_folder(self):
        p = filedialog.askdirectory(title="Select data folder")
        if p: self.var_folder.set(p)

    def iter_files(self):
        base = Path(self.var_folder.get())
        if not base.exists():
            messagebox.showwarning("Data Sweep", f"Folder not found: {base}")
            return []
        return sorted(base.glob(self.var_pattern.get()))

    def make_chunks(self, src: Path):
        rows = self.var_chunk_rows.get()
        if rows <= 0:
            yield src
            return
        overlap = max(0, self.var_overlap.get())
        # stream and write smaller temp files
        with src.open("r", encoding="utf-8", newline="") as f:
            header = f.readline()
            buf = []
            count = 0
            part = 0
            for line in f:
                buf.append(line)
                if len(buf) >= rows:
                    part += 1
                    tmp = Path(tempfile.gettempdir()) / f"{src.stem}_part{part}.csv"
                    with tmp.open("w", encoding="utf-8", newline="") as out:
                        out.write(header); out.writelines(buf)
                    yield tmp
                    if overlap>0:
                        buf = buf[-overlap:]
                    else:
                        buf = []
            if buf:
                part += 1
                tmp = Path(tempfile.gettempdir()) / f"{src.stem}_part{part}.csv"
                with tmp.open("w", encoding="utf-8", newline="") as out:
                    out.write(header); out.writelines(buf)
                yield tmp
