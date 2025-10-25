
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

class ModelLabTab(ttk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Model Lab (internal quick models)")
        self.var_csv = tk.StringVar(value="results\\metrics_latest_features.csv")
        self.var_features = tk.StringVar(value="imbalance queue_pressure mid spread rolling_vol delta_volume")
        self.var_label = tk.StringVar(value="label")
        self.var_model = tk.StringVar(value="LogisticRegression")
        self.var_test_size = tk.DoubleVar(value=0.2)
        self.var_cv = tk.IntVar(value=0)
        self.var_seed = tk.IntVar(value=42)

        r=0
        ttk.Label(self, text="CSV (features+label):").grid(row=r, column=0, sticky="e", padx=6, pady=6)
        ttk.Entry(self, textvariable=self.var_csv, width=60).grid(row=r, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Browse…", command=self._pick_csv).grid(row=r, column=2, padx=6)
        r+=1
        ttk.Label(self, text="Features (space-separated):").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_features, width=60).grid(row=r, column=1, sticky="we", padx=6)
        r+=1
        ttk.Label(self, text="Label column:").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_label, width=20).grid(row=r, column=1, sticky="w", padx=6)
        r+=1
        ttk.Label(self, text="Model:").grid(row=r, column=0, sticky="e", padx=6)
        ttk.Combobox(self, textvariable=self.var_model, values=["LogisticRegression","RandomForest","XGBoost"], width=24, state="readonly").grid(row=r, column=1, sticky="w", padx=6)
        r+=1
        ttk.Label(self, text="Test size / CV folds / Seed:").grid(row=r, column=0, sticky="e", padx=6)
        fr = ttk.Frame(self); fr.grid(row=r, column=1, sticky="w")
        ttk.Entry(fr, textvariable=self.var_test_size, width=8).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left", padx=4)
        ttk.Entry(fr, textvariable=self.var_cv, width=6).pack(side="left")
        ttk.Label(fr, text="/").pack(side="left", padx=4)
        ttk.Entry(fr, textvariable=self.var_seed, width=6).pack(side="left")

    def _pick_csv(self):
        p = filedialog.askopenfilename(title="Select CSV", filetypes=[("CSV","*.csv"),("All","*.*")])
        if p: self.var_csv.set(p)
