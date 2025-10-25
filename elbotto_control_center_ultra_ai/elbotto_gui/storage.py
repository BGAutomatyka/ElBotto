from pathlib import Path
import json

RESULTS_DIR = Path("results")
PARAMS_JSON = RESULTS_DIR / "gui_params.json"
AUTOMATION_JSON = RESULTS_DIR / "automation_state.json"
NEWS_STATE_JSON = RESULTS_DIR / "news_state.json"
BEST_JSON = RESULTS_DIR / "best_config.json"
INDICATORS_JSON = RESULTS_DIR / "selected_indicators.json"

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
    "extra_args": "",
    "append_indicators_flag": False,
    "required_columns": "timestamp,price,volume",
    "automation_mode": "MANUAL",  # MANUAL / AUTO
    "auto_strategy": True,
    "auto_risk": True,
    "auto_news": True
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

def save_automation_state(state: dict):
    _ensure_results()
    AUTOMATION_JSON.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

def load_automation_state():
    try:
        if AUTOMATION_JSON.exists():
            return json.loads(AUTOMATION_JSON.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"mode": DEFAULTS["automation_mode"], "auto_strategy": DEFAULTS["auto_strategy"], "auto_risk": DEFAULTS["auto_risk"], "auto_news": DEFAULTS["auto_news"]}

def save_best(config: dict):
    _ensure_results()
    BEST_JSON.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

def load_best():
    try:
        if BEST_JSON.exists():
            return json.loads(BEST_JSON.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

def save_indicators(selected: list):
    _ensure_results()
    INDICATORS_JSON.write_text(json.dumps({"selected": selected}, ensure_ascii=False, indent=2), encoding="utf-8")

def load_indicators():
    try:
        if INDICATORS_JSON.exists():
            return json.loads(INDICATORS_JSON.read_text(encoding="utf-8")).get("selected", [])
    except Exception:
        pass
    return []
