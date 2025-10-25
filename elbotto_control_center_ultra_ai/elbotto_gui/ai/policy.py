# Adaptive policy: combines market regime, realized vol and news sentiment to tweak params
def suggest_params(base: dict, regime: str, vol: float, news_sent: float, auto_flags: dict):
    out = dict(base)
    # Strategy threshold tweaks: higher for noisy regimes unless news is strongly positive
    if auto_flags.get("auto_strategy", True):
        thr = out.get("threshold", 0.5)
        # regime impact
        if regime == "high_vol": thr += 0.05
        if regime == "low_liquidity": thr += 0.03
        if regime == "calm": thr -= 0.03
        # news sentiment: map [-1,1] -> [-0.05,+0.05]
        thr += 0.05*max(-1.0, min(1.0, news_sent))
        out["threshold"] = round(max(0.1, min(0.9, thr)), 3)
    # Risk sizing
    if auto_flags.get("auto_risk", True):
        r = out.get("risk_per_trade")
        try: r = float(r) if r not in ("", None) else 0.01
        except Exception: r = 0.01
        # shrink risk when vol high or news negative
        r *= (1.0 - min(0.4, max(0.0, (vol-1.0)*0.2)))   # simple vol dampener
        r *= (1.0 - 0.3*max(0.0, -news_sent))            # negative news -> cut risk up to -30%
        out["risk_per_trade"] = round(max(0.001, min(0.05, r)), 4)
        # max position: mirror risk
        mp = float(out.get("max_position", 1.0))
        mp *= 1.0 + 0.3*max(0.0, news_sent)              # positive news -> slight increase
        mp *= 1.0 - 0.3*max(0.0, -news_sent)             # negative news -> decrease
        out["max_position"] = round(max(0.2, min(3.0, mp)), 2)
    return out
