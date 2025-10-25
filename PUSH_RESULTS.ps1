
param([string]$Message = "results upload")
$ErrorActionPreference = "Stop"
if (-not (Test-Path ".git")) { throw "Not a git repo. Run GIT_SETUP_OR_CONNECT.bat first." }
if (-not (Test-Path "results")) { throw "Missing results/ folder." }

$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$branch = "runs/$ts"
git checkout -b $branch
git add -f results/*
git commit -m "run: $ts - $Message"
git push -u origin $branch

Write-Host ""
Write-Host "[OK] Pushed results to branch: $branch"
Write-Host "Open a PR if you want review. Remember: do not store secrets in results/ ."
