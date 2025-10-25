import argparse, json
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--model", default="ProsusAI/finbert")
    a = ap.parse_args()
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
        tok = AutoTokenizer.from_pretrained(a.model)
        mdl = AutoModelForSequenceClassification.from_pretrained(a.model)
        clf = pipeline("sentiment-analysis", model=mdl, tokenizer=tok, top_k=None)
        res = clf(a.text)[0]
        score = res.get('score',0.0)
        label = res.get('label','NEU').lower()
        if 'neg' in label: sent = -abs(score)
        elif 'pos' in label: sent = abs(score)
        else: sent = 0.0
        print(json.dumps({"sentiment":sent, "label":label, "model":a.model}))
    except Exception:
        # Fallback
        POS = ["surge","rally","beat","upgrade","bullish","approval","launch","gain","record","all-time high","partnership","ETF approval"]
        NEG = ["hack","breach","ban","downgrade","bearish","lawsuit","halt","downtime","probe","selloff","liquidation","exploit","bankruptcy"]
        t = a.text.lower(); s=0.0
        for w in POS:
            if w.lower() in t: s += 1.0
        for w in NEG:
            if w.lower() in t: s -= 1.0
        print(json.dumps({"sentiment":max(-1,min(1,s/3.0)),"label":"heuristic","model":"fallback"}))
if __name__ == "__main__":
    main()
