param(
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'

$targets = @(
    "f:\cvn-agent\eval\eval-21-40_demo_v1.0.json",
    "f:\cvn-agent\data\system.txt"
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
