# run_tool.py — uniwersalny starter analiz/backtestu dla ElBotto
# Użycie:
#   python run_tool.py analysis --data data\binance_order_book_small.csv --symbols BTCUSDT ETHUSDT
#   python run_tool.py backtest --data data\binance_order_book_small.csv
#
# Działa tak: szuka w pakiecie 'elbotto/<mode>/' pliku .py z funkcją main()
# lub po prostu uruchamia pierwszy sensowny skrypt (z wyłączeniem __init__.py).
import sys, runpy
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[1] / "src" / "elbotto"

def pick_script(mode: str) -> Path:
    folder = PKG_ROOT / mode
    if not folder.exists():
        print(f"[ERROR] Folder '{folder}' nie istnieje.", file=sys.stderr); sys.exit(2)
    preferred = ["run.py", "signals.py", "feature_importance.py", "main.py", "backtest.py", "analysis.py"]
    for name in preferred:
        cand = folder / name
        if cand.exists():
            return cand
    for cand in folder.glob("*.py"):
        if cand.name != "__init__.py":
            return cand
    print(f"[ERROR] Nie znaleziono skryptu w '{folder}'.", file=sys.stderr); sys.exit(3)

def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("analysis","backtest"):
        print("Użycie: python run_tool.py [analysis|backtest] [--twoje-argumenty]")
        sys.exit(1)
    mode = sys.argv[1]
    script = pick_script(mode)
    sys.argv = [str(script)] + sys.argv[2:]
    print(f"[INFO] Uruchamiam: {script} {' '.join(sys.argv[1:])}")
    runpy.run_path(str(script), run_name='__main__')

if __name__ == '__main__':
    main()
