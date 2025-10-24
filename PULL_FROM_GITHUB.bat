@echo off
chcp 65001 >nul
setlocal
where git >nul 2>nul || (echo [ERROR] Git not found. Install Git and retry.& pause & exit /b 1)
if not exist .git (echo [ERROR] This is not a git repository. Run GIT_SETUP_OR_CONNECT.bat first.& pause & exit /b 1)

echo [INFO] Fetch + pull (rebase, autostash) on the current branch...
git fetch --all --prune
git pull --rebase --autostash

echo.
echo [INFO] Recent commits:
git log --oneline -n 8
pause
endlocal
