"""
Reads results/news_state.json and best_config.json, evaluates rules.json,
produces results/runtime_overrides.json for the bot to hot-reload mid-run.
"""
import time, json, argparse, sys
from pathlib import Path
from rules import load_rules, match_rule, apply_action

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results", help="Results dir produced by GUI")
    ap.add_argument("--interval", type=int, default=5, help="Seconds between checks")
    ap.add_argument("--rules", default="rules.json", help="Rules file (JSON)")
    args = ap.parse_args()

    results = Path(args.results); results.mkdir(exist_ok=True, parents=True)
    news_path = results/"news_state.json"
    best_path = results/"best_config.json"
    out_path  = results/"runtime_overrides.json"
    rules_path= Path(args.rules)

    base = {"threshold": 0.5, "risk_per_trade": 0.01, "max_position": 1.0}
    while True:
        try:
            if best_path.exists():
                try:
                    base.update(json.loads(best_path.read_text(encoding="utf-8")))
                except Exception:
                    pass
            overrides = dict(base)
            # Load rules
            rules = load_rules(rules_path)
            # Load latest news items
            items = []
            if news_path.exists():
                try:
                    st = json.loads(news_path.read_text(encoding="utf-8"))
                    items = st.get("last_items", [])[-50:]
                except Exception:
                    items = []
            # Evaluate rules (most recent first)
            applied = []
            for it in reversed(items):
                for r in rules:
                    if match_rule(r, it):
                        overrides = apply_action(overrides, r.action)
                        applied.append(r.name)
            overrides["applied_rules"] = applied
            overrides["ts"] = time.time()
            out_path.write_text(json.dumps(overrides, ensure_ascii=False, indent=2), encoding="utf-8")
            print("[ADAPTER] wrote", out_path)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print("[ADAPTER][ERR]", repr(e), file=sys.stderr)
        time.sleep(max(1, args.interval))

if __name__ == "__main__":
    main()
