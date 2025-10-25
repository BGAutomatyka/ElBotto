import sys, subprocess, json, shutil
from pathlib import Path

def pip_check(pkg):
    try:
        __import__(pkg)
        return True
    except Exception:
        return False

def main():
    report = {}
    report["python"] = sys.version
    venv = Path(".venv")/"Scripts"/"python.exe"
    report["venv_exists"] = venv.exists()
    report["matplotlib"] = pip_check("matplotlib")
    report["pandas"] = pip_check("pandas")
    report["numpy"] = pip_check("numpy")
    report["feedparser"] = pip_check("feedparser")
    report["transformers"] = pip_check("transformers")
    report["tkinter"] = True  # if this runs in GUI, tkinter loaded

    print(json.dumps(report, indent=2))
    missing = [k for k,v in report.items() if isinstance(v,bool) and not v]
    if missing:
        print("\n[HINT] Missing:", ", ".join(missing))
        print("Install extras: .venv\Scripts\pip install matplotlib pandas numpy feedparser transformers")

if __name__ == "__main__":
    main()
