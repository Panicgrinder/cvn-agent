param(
    [string]$WhatIf = 'true',
    [string]$Confirm = 'false'
)

$whatIfFlag = ($WhatIf -match '^(?i:true|1|\$true)$')
$confirmFlag = ($Confirm -match '^(?i:true|1|\$true)$')

# Phase 4: Entfernen veralteter/duplizierter Dateien
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path | Split-Path -Parent
$targets = @(
    "app/routers/chat_improved.py",
    "app/routers/chat.py",
    "app/routers/health.py",
    "app/routers/roll.py",
    "app/routers/state.py"
)

Write-Host 'Cleanup Phase 4 - Ziel-Dateien:' -ForegroundColor Cyan
foreach ($rel in $targets) {
    $abs = Join-Path $repoRoot $rel
    if (Test-Path $abs) {
    Write-Host (' - ' + $rel) -ForegroundColor Yellow
    } else {
    Write-Host (' - ' + $rel + ' (nicht gefunden)') -ForegroundColor DarkGray
    }
}

if ($whatIfFlag -or -not $confirmFlag) {
    Write-Host 'WhatIf aktiv oder keine Bestätigung: Es werden keine Dateien gelöscht.' -ForegroundColor Cyan
    Write-Host 'Ausführung zum Löschen: powershell -File scripts/cleanup_phase4.ps1 -WhatIf:$false -Confirm:$true' -ForegroundColor DarkCyan
    exit 0
}

foreach ($rel in $targets) {
    $abs = Join-Path $repoRoot $rel
    if (Test-Path $abs) {
        try {
            Remove-Item -LiteralPath $abs -Force
            Write-Host ('Gelöscht: ' + $rel) -ForegroundColor Green
        } catch {
            Write-Host ('Fehler beim Löschen: ' + $rel + ' -> ' + $_.Exception.Message) -ForegroundColor Red
        }
    }
}

Write-Host 'Cleanup Phase 4 abgeschlossen.' -ForegroundColor Green
