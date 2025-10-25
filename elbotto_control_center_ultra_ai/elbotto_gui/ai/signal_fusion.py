# Combines signals from NewsEngine + Regime metrics into a single scalar per symbol
def fuse(news_score: float, regime_strength: float, weight_news=0.6):
    # Exponential smoothing-like blend
    weight_news = max(0.0, min(1.0, weight_news))
    return weight_news*news_score + (1.0-weight_news)*regime_strength
