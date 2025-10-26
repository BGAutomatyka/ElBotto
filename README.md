# Alpha Bot — clean start

Ten branch to **czysta baza** pod front web (React + Vite) + deploy na **GitHub Pages**.

## Lokalnie
```bash
cd apps/web-game
npm i
npm run dev
```

## Deploy na Pages
- W repo ustaw **Settings → Pages → Build and deployment → Source: GitHub Actions**.
- Ten workflow buduje i publikuje **branch `clean/alpha-pages`**.
- Adres będzie: `https://<twoj-user>.github.io/<nazwa-repo>/`

## Co dalej
- Dodajemy real-time WS/API i UI (tabs: Live, Backtest, Rules).
- Spięcie z płatnościami przez endpoint webhook (na backendzie).
