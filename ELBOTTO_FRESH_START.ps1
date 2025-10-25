# ================================
# ELBOTTO_FRESH_START.ps1
# Fresh clone + venv + install + run GUI
# ================================
param(
  [string]$RepoUrl = "https://github.com/BGAutomatyka/ElBotto.git",
  [string]$Target  = "C:\Dev\ElBotto"
)

Write-Host "[INFO] Fresh start for ElBotto" -ForegroundColor Cyan
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force | Out-Null

# 1) Katalog docelowy (poza OneDrive)
if (!(Test-Path $Target)) { New-Item -ItemType Directory -Force -Path $Target | Out-Null }
Set-Location $Target

# 2) Git
$gitOK = $true
try { git --version | Out-Null } catch { $gitOK = $false }
if (-not $gitOK) {
  Write-Host "[ERROR] Git nie znaleziony. Zainstaluj Git for Windows i uruchom ponownie." -ForegroundColor Red
  exit 1
}

# 3) Pobieramy repo (jeśli brak .git) albo twardo aktualizujemy do origin/main
if (!(Test-Path ".git")) {
  Write-Host "[GIT] Cloning $RepoUrl ..." -ForegroundColor Yellow
  git clone $RepoUrl . || (Write-Host "[ERROR] git clone nie powiódł się." -ForegroundColor Red; exit 1)
} else {
  Write-Host "[GIT] Fetch + hard reset to origin/main ..." -ForegroundColor Yellow
  git fetch --all
  git reset --hard origin/main
}

# 4) VENV na najnowszym dostępnym Pythonie (3.13 -> 3.11 -> 3.10)
if (Test-Path ".venv") { Remove-Item -Recurse -Force .venv }
$created = $false
foreach ($ver in @("3.13","3.11","3.10")) {
  try {
    Write-Host "[PY] Tworzenie venv na Pythonie $ver ..." -ForegroundColor Yellow
    py -$ver -m venv .venv 2>$null
    if (Test-Path ".venv\Scripts\python.exe") { $created = $true; break }
  } catch { }
}
if (-not $created) {
  Write-Host "[ERROR] Nie udało się utworzyć venv (brak Pythona 3.10+). Zainstaluj Python 3.11 lub 3.13 (x64)." -ForegroundColor Red
  exit 1
}

# 5) Aktywacja + instalacja
& .\.venv\Scripts\python.exe -V
$env:PRE_COMMIT_ALLOW_NO_CONFIG = "1"   # ucisza komunikaty pre-commit w GUI Desktop

Write-Host "[PIP] Aktualizacja pip/setuptools/wheel ..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip install -U pip setuptools wheel

Write-Host "[PIP] Usuwam stare 'elbotto' (jeśli jest) i instaluję z lokalnego źródła ..." -ForegroundColor Yellow
& .\.venv\Scripts\python.exe -m pip uninstall -y elbotto | Out-Null
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"

# 6) Kontrola z jakiej ścieżki ładuje się pakiet
& .\.venv\Scripts\python.exe - << 'PY'
import elbotto, pathlib, sys
print("[CHECK] elbotto from:", pathlib.Path(elbotto.__file__).resolve())
print("[CHECK] Python:", sys.version)
PY

# 7) Start GUI
Write-Host "[RUN] Uruchamiam GUI..." -ForegroundColor Cyan
& .\.venv\Scripts\python.exe -m elbotto.gui.app
