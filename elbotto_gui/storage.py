
from pathlib import Path
import json

RESULTS_DIR = Path("results")
PARAMS_JSON = RESULTS_DIR / "gui_params.json"
PROFILES_JSON = RESULTS_DIR / "gui_profiles.json"

DEFAULTS = {
    "dataset": "data\\binance_order_book_small.csv",
    "symbols": "BTCUSDT ETHUSDT",
    "threshold": 0.50,
    "capital": 5000.0,
    "max_position": 1.0,
    "fee": 0.0002,
    "windows": "3 6 9",
    "spread_max": "",
    "tp_bps": "",
    "sl_bps": "",
    "risk_per_trade": "",
    "analysis_script": "run_quickstart_tuned.py",
    "backtest_script": "src\\elbotto\\backtest\\backtest.py",
    "train_script": "src\\elbotto\\ml\\train.py",
    "paper_script": "src\\elbotto\\bots\\paper.py",
    "live_script": "src\\elbotto\\bots\\live.py",
    "api_key": "",
    "api_secret": "",
    "env": "paper",
    "extra_args": ""
}

def _ensure_results():
    RESULTS_DIR.mkdir(exist_ok=True, parents=True)

def load_params():
    try:
        if PARAMS_JSON.exists():
            return json.loads(PARAMS_JSON.read_text(encoding="utf-8"))
    except Exception:
        pass
    return DEFAULTS.copy()

def save_params(p: dict):
    _ensure_results()
    PARAMS_JSON.write_text(json.dumps(p, ensure_ascii=False, indent=2), encoding="utf-8")

def load_profiles():
    if PROFILES_JSON.exists():
        try:
            return json.loads(PROFILES_JSON.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_profiles(d: dict):
    _ensure_results()
    PROFILES_JSON.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
