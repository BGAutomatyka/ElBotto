import json
from pathlib import Path
import pandas as pd

f = Path("results/lob_features_live.csv")
df = pd.read_csv(f)
# bierzemy ostatnie ~50k próbek (bezpiecznie, jeśli plik rośnie)
df = df.tail(50000)
thr = float(df["microprice_imb"].abs().quantile(0.97))  # cel: ~3% ticków generuje sygnał
suggest = {
    "threshold": round(max(0.02, thr), 6),
    "risk_per_trade": 0.005,
    "max_position": 2
}
p = Path("results/runtime_overrides.json")
current = {}
if p.exists():
    current = json.loads(p.read_text(encoding="utf-8"))
current.update(suggest)
p.write_text(json.dumps(current, indent=2), encoding="utf-8")
print("Suggested:", suggest)
