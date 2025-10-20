param(
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'

# Basis: aktuelles Skriptverzeichnis → Projektwurzel ist dessen Elternordner
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

$targets = @(
    # Top-Level eval/ Duplikate entfernen (Demo/Fantasy, json/jsonl)
    Join-Path $ProjectRoot 'eval\eval-21-40_demo_v1.0.json',
    Join-Path $ProjectRoot 'eval\eval-21-40_demo_v1.0.jsonl',
    Join-Path $ProjectRoot 'eval\eval-21-40_fantasy_v1.0.json',
    Join-Path $ProjectRoot 'eval\eval-21-40_fantasy_v1.0.jsonl',
    # Historische Prompt-Datei
    Join-Path $ProjectRoot 'data\system.txt'
)

foreach ($t in $targets) {
    if (Test-Path $t) {
        if ($WhatIf) {
            Write-Host "[WhatIf] Would remove: $t"
        } else {
            Remove-Item -Path $t -Force
            Write-Host "Removed: $t"
        }
    } else {
        Write-Host "Skip (not found): $t"
    }
}
