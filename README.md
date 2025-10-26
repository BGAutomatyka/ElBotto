# ElBotto

**LIVE (fallback, no-build):** https://bgautomatyka.github.io/ElBotto/

## PRO app (React + Vite)
- source: `apps/web-pro`
- build: GitHub Pages via Actions (workflow: `.github/workflows/pro-pages.yml`)
- entry: `/apps/web-pro/index.html`

### Local dev
```bash
cd apps/web-pro
npm i
npm run dev
```

### Deploy
Push to `main` (paths under `apps/web-pro/**`) — Actions will build and publish to GitHub Pages.

## Fallback `/docs`
Statyczna wersja działająca bez Node — do szybkiego podglądu.

---

### Roadmap (skrót)
- [x] HUD + wskaźniki (SMA/EMA/BB/MACD/RSI), log, KPI, avatar, eksport CSV (docs)
- [x] PRO skeleton (React + Lightweight Charts)
- [ ] Equity/DD panel w PRO, tabele transakcji, presety, rules builder
- [ ] Backtest import CSV, metryki (Sharpe/Sortino/CAGR/MAR)
- [ ] Integracje (websocket feed, giełdy)
