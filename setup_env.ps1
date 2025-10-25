Write-Host "`n=== ElBotto – setup/uruchomienie (PowerShell) ===`n"
Set-Location -Path $PSScriptRoot

try {
    Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
} catch {}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python 3.11+ nie został znaleziony w PATH. Zainstaluj go z opcją Add to PATH."
    exit 1
}

if (-not (Test-Path ".\.venv")) {
    Write-Host "[INFO] Tworzenie .venv..."
    python -m venv .venv
} else {
    Write-Host "[INFO] Wykryto istniejące środowisko .venv"
}

$py = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    Write-Host "Nie znaleziono $py"
    exit 1
}

& $py -m pip install --upgrade pip setuptools wheel

if (Test-Path ".\pyproject.toml") {
    Write-Host "[INFO] Instalacja wg pyproject.toml..."
    try {
        & $py -m pip install -e .[dev]
    } catch {
        & $py -m pip install -e .
    }
}
elseif (Test-Path ".\requirements.txt") {
    Write-Host "[INFO] Instalacja wg requirements.txt..."
    & $py -m pip install -r requirements.txt
}
else {
    Write-Host "[UWAGA] Nie znaleziono plików zależności – pomijam instalację."
}

Write-Host "`n[INFO] Uruchamianie ElBotto..."
if (Test-Path ".\src\elbotto\__main__.py") {
    & $py .\src\elbotto\__main__.py
}
else {
    & $py -m elbotto
}
Write-Host "`n[GOTOWE] Uruchomienie zakończone.`n"
