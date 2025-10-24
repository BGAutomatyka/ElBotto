import time, threading, queue, json, re
from pathlib import Path

class SimpleSentiment:
    POS = {"surge","rally","beat","upgrade","bullish","approval","launch","gain","record","all-time high","partnership","ETF approval"}
    NEG = {"hack","breach","ban","downgrade","bearish","lawsuit","halt","downtime","probe","selloff","liquidation","exploit","bankruptcy"}
    def score(self, text: str) -> float:
        t = text.lower()
        s = 0.0
        for w in self.POS:
            if w in t: s += 1.0
        for w in self.NEG:
            if w in t: s -= 1.0
        return max(-3.0, min(3.0, s))/3.0  # normalize to [-1,1]

class NewsEngine:
    def __init__(self, results_dir: Path):
        self.results_dir = results_dir; self.results_dir.mkdir(exist_ok=True, parents=True)
        self.queue = queue.Queue()
        self.running = False
        self.sources = []  # list of dict: {"type":"rss/csv","url/path":str,"symbols":["BTCUSDT"],"include":[],"exclude":[]}
        self.sentiment = SimpleSentiment()
        self.state = {"per_symbol": {}, "last_items": []}  # rolling

    def add_source(self, src: dict):
        self.sources.append(src)

    def start(self, interval_sec=60):
        if self.running: return
        self.running = True
        threading.Thread(target=self._worker, args=(interval_sec,), daemon=True).start()

    def stop(self):
        self.running = False

    def _emit(self, item):
        self.state["last_items"] = (self.state.get("last_items", []) + [item])[-200:]
        for sym in item.get("symbols", []):
            s = self.state["per_symbol"].setdefault(sym, {"sent":0.0, "n":0})
            s["sent"] = 0.85*s["sent"] + 0.15*item.get("sentiment",0.0)  # EMA smoothing
            s["n"] += 1
        self.queue.put(item)
        # persist
        (self.results_dir/"news_state.json").write_text(json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8")

    def _worker(self, interval):
        while self.running:
            try:
                for src in self.sources:
                    if src.get("type") == "rss":
                        self._poll_rss(src)
                    elif src.get("type") == "csv":
                        self._poll_csv(src)
            except Exception as e:
                self.queue.put({"type":"error","error":repr(e)})
            time.sleep(max(5, int(interval)))

    def _match_symbols(self, text, fallback_syms):
        syms = set(fallback_syms or [])
        if "btc" in text.lower(): syms.add("BTCUSDT")
        if "eth" in text.lower(): syms.add("ETHUSDT")
        return list(syms)

    def _poll_rss(self, src):
        try:
            import feedparser  # optional
        except Exception:
            return
        feed = feedparser.parse(src.get("url"))
        inc = [w.lower() for w in src.get("include", [])]
        exc = [w.lower() for w in src.get("exclude", [])]
        for e in feed.entries[:20]:
            title = e.get("title","")
            ll = title.lower()
            if inc and not any(w in ll for w in inc): continue
            if exc and any(w in ll for w in exc): continue
            s = self.sentiment.score(title)
            syms = self._match_symbols(title, src.get("symbols",[]))
            item = {"type":"rss","title":title,"link":e.get("link",""),"sentiment":s,"symbols":syms,"ts":e.get("published","")}
            self._emit(item)

    def _poll_csv(self, src):
        # Expect columns: ts,source,headline,sentiment(optional),symbols(optional; space-separated)
        path = Path(src.get("path",""))
        if not path.exists(): return
        try:
            import csv
            with path.open("r", encoding="utf-8") as f:
                rd = csv.DictReader(f)
                for row in list(rd)[-50:]:
                    s = float(row.get("sentiment","0") or 0)
                    syms = row.get("symbols","").split() if row.get("symbols") else self._match_symbols(row.get("headline",""), src.get("symbols",[]))
                    item = {"type":"csv","title":row.get("headline",""),"link":row.get("source",""),"sentiment":s,"symbols":syms,"ts":row.get("ts","")}
                    self._emit(item)
        except Exception:
            return

    def get_symbol_sentiment(self, sym):
        return float(self.state.get("per_symbol",{}).get(sym,{}).get("sent",0.0))
