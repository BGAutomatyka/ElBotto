"""
Drop this into your trading loop to hot-reload overrides mid-run.
"""
import json, time
from pathlib import Path

class Overrides:
    def __init__(self, path="results/runtime_overrides.json", refresh_sec=3):
        self.path = Path(path); self.refresh_sec = refresh_sec
        self.last_ts = 0.0; self.data = {}
    def tick(self):
        try:
            if self.path.exists():
                st = self.path.stat().st_mtime
                if st > self.last_ts:
                    self.data = json.loads(self.path.read_text(encoding="utf-8"))
                    self.last_ts = st
        except Exception:
            pass
    def get(self, key, default=None):
        return self.data.get(key, default)
    def paused(self):
        pu = self.data.get("pause_until")
        return pu is not None and time.time() < float(pu)

# Example usage in your bot loop:
# overrides = Overrides()
# while running:
#     overrides.tick()
#     if overrides.paused(): 
#         sleep(1); continue
#     thr = overrides.get("threshold", current_threshold)
#     risk = overrides.get("risk_per_trade", current_risk)
#     maxpos = overrides.get("max_position", current_maxpos)
#     # apply to your signal calc and risk sizing...
