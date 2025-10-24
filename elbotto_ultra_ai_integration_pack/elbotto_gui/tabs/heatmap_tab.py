import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess, shlex, os

class HeatmapTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Order Book Heatmap")
        self.var_csv = tk.StringVar(value="results\\lob_features.csv")
        self.var_levels = tk.IntVar(value=10)
        self.var_out = tk.StringVar(value="results\\ob_heatmap.png")

        r=0
        ttk.Label(self, text="Features CSV:").grid(row=r, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_csv, width=70).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self, text="...", command=self._pick_csv).grid(row=r, column=2, padx=4); r+=1

        ttk.Label(self, text="Levels:").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_levels, width=8).grid(row=r, column=1, sticky="w")
        ttk.Label(self, text="Out PNG:").grid(row=r, column=2, sticky="e")
        ttk.Entry(self, textvariable=self.var_out, width=25).grid(row=r, column=3, sticky="w"); r+=1

        ttk.Button(self, text="Render", command=self._run).grid(row=r, column=0, padx=6, pady=8)
        ttk.Button(self, text="Open image", command=self._open_img).grid(row=r, column=1, sticky="w", padx=6, pady=8)
        self.grid_columnconfigure(1, weight=1)

    def _pick_csv(self):
        p = filedialog.askopenfilename(title="Features CSV", filetypes=[("CSV","*.csv"),("All","*.*")])
        if p: self.var_csv.set(p)

    def _open_img(self):
        try:
            os.startfile(self.var_out.get())
        except Exception:
            messagebox.showinfo("Heatmap","File not found.")

    def _run(self):
        cmd = f".venv\\Scripts\\python.exe -m elbotto_patch.viz.ob_heatmap --csv {self.var_csv.get()} --levels {self.var_levels.get()} --out {self.var_out.get()}"
        try:
            import subprocess, shlex
            subprocess.Popen(shlex.split(cmd))
            messagebox.showinfo("Heatmap","Rendering… PNG trafi do wskazanej ścieżki.")
        except Exception as e:
            messagebox.showerror("Heatmap", repr(e))
