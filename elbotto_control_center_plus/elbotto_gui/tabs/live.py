
import tkinter as tk
from tkinter import ttk, filedialog

class LiveTab(ttk.LabelFrame):
    def __init__(self, master, var_paper_script, var_live_script, var_env, var_api_key, var_api_secret):
        super().__init__(master, text="Paper / Live")
        self.var_paper_script = var_paper_script
        self.var_live_script  = var_live_script
        self.var_env = var_env; self.var_env.set("paper")
        self.var_api_key = var_api_key
        self.var_api_secret = var_api_secret

        ttk.Radiobutton(self, text="Paper", variable=self.var_env, value="paper").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        ttk.Radiobutton(self, text="Live",  variable=self.var_env, value="live").grid(row=0, column=1, sticky="w", padx=6, pady=6)

        ttk.Label(self, text="Paper script:").grid(row=1, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_paper_script, width=60).grid(row=1, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Browse…", command=lambda:self._pick(self.var_paper_script)).grid(row=1, column=2, padx=6)

        ttk.Label(self, text="Live script:").grid(row=2, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_live_script, width=60).grid(row=2, column=1, sticky="we", padx=6)
        ttk.Button(self, text="Browse…", command=lambda:self._pick(self.var_live_script)).grid(row=2, column=2, padx=6)

        ttk.Label(self, text="API Key:").grid(row=3, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_api_key, width=40, show="•").grid(row=3, column=1, sticky="w", padx=6)
        ttk.Label(self, text="API Secret:").grid(row=4, column=0, sticky="e", padx=6)
        ttk.Entry(self, textvariable=self.var_api_secret, width=40, show="•").grid(row=4, column=1, sticky="w", padx=6)

    def _pick(self, var):
        p = filedialog.askopenfilename(title="Select Python script", filetypes=[("Python","*.py"),("All","*.*")])
        if p: var.set(p)
