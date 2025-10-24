import argparse, csv, math, random
from collections import defaultdict

class LinUCB:
    def __init__(self, n_features, alpha=1.0):
        import numpy as np
        self.n = n_features; self.alpha=alpha
        self.A = defaultdict(lambda: np.identity(self.n))
        self.b = defaultdict(lambda: np.zeros((self.n,1)))
    def select(self, ctx, actions):
        import numpy as np
        x = np.array(ctx).reshape(-1,1)
        best_a=None; best_ucb=-1e9
        for a in actions:
            A = self.A[a]; b = self.b[a]
            A_inv = np.linalg.inv(A); theta = A_inv @ b
            p = (theta.T @ x + self.alpha * math.sqrt((x.T @ A_inv @ x).item())).item()
            if p>best_ucb: best_ucb=p; best_a=a
        return best_a
    def update(self, ctx, a, reward):
        import numpy as np
        x = np.array(ctx).reshape(-1,1)
        self.A[a] += x @ x.T
        self.b[a] += reward * x

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--context-cols", nargs="+", required=True)
    ap.add_argument("--reward-col", required=True)
    ap.add_argument("--actions", nargs="+", default=["thr_low","thr_mid","thr_high"])
    ap.add_argument("--alpha", type=float, default=0.8)
    a = ap.parse_args()
    import pandas as pd
    df = pd.read_csv(a.csv).dropna()
    ctx = df[a.context_cols].values.tolist()
    rew = df[a.reward_col].values.tolist()
    bandit = LinUCB(n_features=len(a.context_cols), alpha=a.alpha)
    actions = a.actions
    chosen = []
    for c, r in zip(ctx, rew):
        act = bandit.select(c, actions)
        bandit.update(c, act, float(r))
        chosen.append(act)
    out = a.csv.replace(".csv","_bandit_actions.csv")
    pd.DataFrame({"action": chosen}).to_csv(out, index=False)
    print("[BANDIT] wrote", out)

if __name__ == "__main__":
    main()
