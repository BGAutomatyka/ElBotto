# ElBotto — Browser Game (Alpha)

**Prototyp SPA** gry treningowej dla bota. Działa bez backendu (symulacja), ale potrafi połączyć się do `/ws` backendu alfa.

## Szybki start
```bash
pnpm i
pnpm dev
```
Otwórz: http://127.0.0.1:5173

## Build
```bash
pnpm build
```
Artefakty w `dist/` — można serwować statycznie (Nginx).

## Połączenie z backendem
Włącz w UI przełącznik **Live feed (WS)**. Backend FastAPI musi wystawiać `/ws` zgodnie z modułem `alpha`.
