@echo off
chcp 65001 >nul
setlocal
echo [INFO] Connecting local folder to GitHub repo: https://github.com/BGAutomatyka/ElBotto.git
where git >nul 2>nul || (echo [ERROR] Git not found. Install Git and retry.& pause & exit /b 1)

if not exist .git (
  echo [INFO] Initializing git repo...
  git init
  echo [INFO] Making a local baseline commit (so your files are saved before pulling remote)...
  git add .
  git commit -m "local baseline before connecting remote" 1>nul 2>nul
)

for /f "tokens=2*" %%A in ('git remote -v ^| findstr /r "^origin[ ]"') do set HAS_ORIGIN=1
if "%HAS_ORIGIN%"=="" (
  git remote add origin https://github.com/BGAutomatyka/ElBotto.git
) else (
  git remote set-url origin https://github.com/BGAutomatyka/ElBotto.git
)

echo [INFO] Fetching from origin...
git fetch origin

REM Ensure main exists and is checked out
git rev-parse --verify refs/heads/main >nul 2>nul || git branch -m master main 2>nul
git checkout -B main 2>nul

echo [INFO] Pulling (rebase + autostash)...
git pull --rebase --autostash origin main || (
  echo.
  echo [WARN] Pull reported conflicts. Resolve in your editor, then run:
  echo        git add <files>  &&  git rebase --continue
  echo        or cancel: git rebase --abort
  pause
  exit /b 1
)

echo [OK] Connected and up to date with origin/main.
git log --oneline -n 5
pause
endlocal
