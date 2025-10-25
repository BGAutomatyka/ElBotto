import csv, random, math
from pathlib import Path

def main():
    out = Path("data/toy_lob.csv"); out.parent.mkdir(parents=True, exist_ok=True)
    rnd = random.Random(1337)
    price = 30000.0
    with out.open("w", newline="", encoding="utf-8") as f:
        cols = ["ts","bid1","ask1","bid1_qty","ask1_qty","bid2","ask2","bid2_qty","ask2_qty","bid3","ask3","bid3_qty","ask3_qty"]
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for t in range(0, 200000):
            drift = rnd.gauss(0, 0.5)
            price = max(100.0, price + drift)
            spread = 0.5 + abs(rnd.gauss(0,0.05))
            bid = price - spread/2; ask = price + spread/2
            row = {
                "ts": t,
                "bid1": round(bid,2), "ask1": round(ask,2),
                "bid1_qty": round(10 + rnd.random()*50,3), "ask1_qty": round(10 + rnd.random()*50,3),
                "bid2": round(bid-0.5,2), "ask2": round(ask+0.5,2),
                "bid2_qty": round(10 + rnd.random()*40,3), "ask2_qty": round(10 + rnd.random()*40,3),
                "bid3": round(bid-1.0,2), "ask3": round(ask+1.0,2),
                "bid3_qty": round(10 + rnd.random()*30,3), "ask3_qty": round(10 + rnd.random()*30,3),
            }
            w.writerow(row)
    print("[TOY] wrote", out)

if __name__ == "__main__":
    main()
