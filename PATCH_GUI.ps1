
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "[PATCH] Patching elbotto_gui\app.py (imports + tabs)..."

$app = Join-Path (Get-Location) "elbotto_gui\app.py"
if (!(Test-Path $app)) {
  Write-Warning "[PATCH] elbotto_gui\app.py not found. Skipping (non-fatal)."
  exit 0
}

$content = Get-Content $app -Raw -ErrorAction Stop

# Ensure imports
$imports = @(
  "from elbotto_gui.tabs.wfv_tab import WFVTab",
  "from elbotto_gui.tabs.heatmap_tab import HeatmapTab",
  "from elbotto_gui.tabs.adapter_tab import AdapterPlusTab",
  "from elbotto_gui.tabs.rules_editor_tab import RulesEditorTab",
  "from elbotto_gui.tabs.selftest_tab import SelfTestTab"
)

foreach ($imp in $imports) {
  if ($content -notmatch [regex]::Escape($imp)) {
    $content = $imp + "`r`n" + $content
    Write-Host "[PATCH] Added import: $imp"
  } else {
    Write-Host "[PATCH] Import already present: $imp"
  }
}

# Ensure Notebook adds
$adds = @(
  "self.nb.add(WFVTab(self.nb), text=\"WFV\")",
  "self.nb.add(HeatmapTab(self.nb), text=\"Heatmap\")",
  "self.nb.add(AdapterPlusTab(self.nb), text=\"Adapter+\")",
  "self.nb.add(RulesEditorTab(self.nb), text=\"Rules\")",
  "self.nb.add(SelfTestTab(self.nb), text=\"Self-Test\")"
)

if ($content -match "self\.nb\s*=\s*ttk\.Notebook") {
  # Try to inject after first self.nb.add occurrence or after nb creation
  $lines = $content -split "`r?`n"
  $out = New-Object System.Collections.Generic.List[string]
  $injected = $false
  for ($i=0; $i -lt $lines.Count; $i++) {
    $out.Add($lines[$i])
    if (-not $injected -and $lines[$i] -match "self\.nb\s*=\s*ttk\.Notebook") {
      # scan forward a bit to find where tabs are being added; inject after pack or after a few lines
      $j = $i
      while ($j -lt $lines.Count -and $lines[$j] -notmatch "self\.nb\.pack") { $out.Add($lines[$j]); $j++ }
      if ($j -lt $lines.Count) { $out.Add($lines[$j]); $j++ }
      # Avoid duplicates
      foreach ($add in $adds) {
        if ($content -notmatch [regex]::Escape($add)) {
          $out.Add("        " + $add)
          Write-Host "[PATCH] Added tab: $add"
        } else {
          Write-Host "[PATCH] Tab already present: $add"
        }
      }
      # copy the rest
      for (; $j -lt $lines.Count; $j++) { $out.Add($lines[$j]) }
      $content = [string]::Join("`r`n", $out)
      $injected = $true
      break
    }
  }
  if (-not $injected) {
    # Append at end
    $content += "`r`n# --- Auto-added tabs ---`r`n"
    foreach ($add in $adds) {
      if ($content -notmatch [regex]::Escape($add)) {
        $content += "        $add`r`n"
        Write-Host "[PATCH] Appended tab: $add"
      }
    }
  }
} else {
  # Append at end if nb not found
  $content += "`r`n# NOTE: Could not locate Notebook creation; tabs appended may require manual placement.`r`n"
  foreach ($add in $adds) {
    if ($content -notmatch [regex]::Escape($add)) {
      $content += "        $add`r`n"
      Write-Host "[PATCH] Appended (fallback) tab: $add"
    }
  }
}

Set-Content -Path $app -Value $content -Encoding UTF8
Write-Host "[PATCH] Done."
