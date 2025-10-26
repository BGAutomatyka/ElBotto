@echo off
setlocal ENABLEDELAYEDEXPANSION
REM === Start ElBotto Web Game (DEV) ===
cd /d %~dp0
IF NOT EXIST apps\web-game (
  echo [ERROR] Folder apps\web-game nie istnieje. Upewnij sie, ze wypakowales cale repo.
  pause
  exit /b 1
)
cd apps\web-game
where node >nul 2>&1 || (
  echo [ERROR] Nie znaleziono Node.js. Zainstaluj z: https://nodejs.org/en/download/
  pause
  exit /b 1
)
IF EXIST package-lock.json (
  echo [INFO] Instalacja zaleznosci (npm ci)...
  npm ci
) ELSE (
  echo [INFO] Instalacja zaleznosci (npm i)...
  npm i
)
set PORT=5173
echo [INFO] Uruchamiam Vite dev server...
start "ElBotto Web Game" cmd /c "npm run dev"
REM Autootwarcie przegladarki (moze byc inny port, domyslnie 5173)
start "" http://127.0.0.1:5173
pause
