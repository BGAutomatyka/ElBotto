@echo off
setlocal
cd /d %~dp0
where node >nul 2>&1 || (
  echo [ERROR] Node.js wymagany: https://nodejs.org/en/download/
  pause
  exit /b 1
)
IF EXIST package-lock.json (
  npm ci
) ELSE (
  npm i
)
echo [INFO] Buduje produkcyjnie...
npm run build
IF %ERRORLEVEL% NEQ 0 (
  echo [ERROR] Build nie powiodl sie.
  pause
  exit /b 1
)

echo [INFO] Podglad dist/ na http://127.0.0.1:5173
where npx >nul 2>&1 && (
  npx serve -s dist -l 5173
) || (
  where python >nul 2>&1 && (
    python -m http.server 5173 -d dist
  ) || (
    echo [ERROR] Brak npx i python. Zainstaluj jeden z nich, aby wystawic katalog dist/.
    pause
  )
)
