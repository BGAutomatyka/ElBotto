
# quick_models.py — proste modele predykcyjne na CSV (sklearn / xgboost, jeśli dostępny)
import argparse, json, sys
from pathlib import Path

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", required=True)
    p.add_argument("--features", nargs="+", required=True)
    p.add_argument("--label", required=True)
    p.add_argument("--model", choices=["LogisticRegression","RandomForest","XGBoost"], default="LogisticRegression")
    p.add_argument("--test-size", type=float, default=0.2)
    p.add_argument("--cv", type=int, default=0)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--outdir", default="results/models")
    args = p.parse_args()

    import pandas as pd
    df = pd.read_csv(args.csv)
    X = df[args.features]
    y = df[args.label]

    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, roc_auc_score, f1_score, classification_report
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier

    model = None
    if args.model == "LogisticRegression":
        model = LogisticRegression(max_iter=200, random_state=args.seed, n_jobs=None)
    elif args.model == "RandomForest":
        model = RandomForestClassifier(n_estimators=200, random_state=args.seed, n_jobs=-1)
    elif args.model == "XGBoost":
        try:
            from xgboost import XGBClassifier
            model = XGBClassifier(
                n_estimators=400, max_depth=6, learning_rate=0.05, subsample=0.9, colsample_bytree=0.9,
                random_state=args.seed, n_jobs=-1, tree_method="hist"
            )
        except Exception:
            print("[WARN] xgboost not installed, falling back to RandomForest.", file=sys.stderr)
            from sklearn.ensemble import RandomForestClassifier
            model = RandomForestClassifier(n_estimators=200, random_state=args.seed, n_jobs=-1)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=args.test_size, random_state=args.seed, stratify=y)

    metrics = {}
    if args.cv and args.cv > 1:
        scores = cross_val_score(model, X, y, cv=args.cv, scoring="roc_auc")
        metrics["cv_mean_roc_auc"] = float(scores.mean())
        metrics["cv_std_roc_auc"] = float(scores.std())

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    try:
        y_prob = model.predict_proba(X_test)[:,1]
        metrics["roc_auc"] = float(roc_auc_score(y_test, y_prob))
    except Exception:
        metrics["roc_auc"] = None
    metrics["accuracy"] = float(accuracy_score(y_test, y_pred))
    metrics["f1"] = float(f1_score(y_test, y_pred))

    outdir = Path(args.outdir); outdir.mkdir(parents=True, exist_ok=True)
    # save metrics
    (outdir/"metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    try:
        import joblib
        joblib.dump(model, outdir/"model.pkl")
    except Exception:
        pass

    print("[MODEL] metrics:", json.dumps(metrics))

if __name__ == "__main__":
    main()
