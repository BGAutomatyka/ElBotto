
param([int]$Minutes = 5)
$ErrorActionPreference = "SilentlyContinue"
if (-not (Test-Path ".git")) { Write-Host "Not a git repo." ; exit 1 }
while ($true) {
  try {
    git fetch --all --prune | Out-Null
    git pull --rebase --autostash | Out-Null
    Write-Host ("[{0}] pulled" -f (Get-Date))
  } catch {
    Write-Host ("[{0}] pull failed: {1}" -f (Get-Date), $_.Exception.Message)
  }
  Start-Sleep -Seconds ($Minutes*60)
}
