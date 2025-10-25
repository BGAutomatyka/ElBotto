Param([string]$AppPath = "elbotto_gui\app.py")

if (-not (Test-Path $AppPath)) { Write-Host "[PATCH] $AppPath not found."; exit 1 }
$content = Get-Content $AppPath -Raw

$import = "from elbotto_gui.tabs.control_tab import ControlTab"
if ($content -notmatch [regex]::Escape($import)) {
  $content = $import + "`r`n" + $content
  Write-Host "[PATCH] Added ControlTab import"
}

$add = "self.nb.add(ControlTab(self.nb), text=""Control"")"
if ($content -match "self\.nb\s*=\s*ttk\.Notebook") {
  if ($content -notmatch [regex]::Escape($add)) {
    $content += "`r`n        $add"
    Write-Host "[PATCH] Added Control tab to Notebook"
  }
} else {
  if ($content -notmatch [regex]::Escape($add)) {
    $content += "`r`n# NOTE: Manual placement may be required`r`n        $add"
    Write-Host "[PATCH] Appended Control tab (manual placement may be required)"
  }
}

Set-Content -Path $AppPath -Value $content -Encoding UTF8
Write-Host "[PATCH] Done."
