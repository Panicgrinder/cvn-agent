# Requires: git; optional: git-filter-repo on PATH
param(
    [switch]$WhatIf,
    [string]$Token = 'Docker',
    [string]$RepoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-Tool($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        throw "Missing required tool: $name"
    }
}

Assert-Tool git

Push-Location $RepoRoot
try {
    $isGit = (git rev-parse --is-inside-work-tree) -eq 'true'
    if (-not $isGit) { throw "Not a git repository: $RepoRoot" }

    $hasFilterRepo = Get-Command git-filter-repo -ErrorAction SilentlyContinue
    if (-not $hasFilterRepo) {
        Write-Warning 'git-filter-repo not found. Install via: pip install git-filter-repo'
    }

    Write-Host "Preparing docs-only history rewrite plan for token: '$Token'" -ForegroundColor Cyan
    Write-Host 'Scope include: docs/**, README.md, DONELOG/CHANGELOG-like files' -ForegroundColor DarkGray
    Write-Host 'Scope exclude: eval/**, app/**, scripts/**, datasets' -ForegroundColor DarkGray

    $replaceSpec = @()
    $replaceSpec += "regex:${Token}==>"  # remove token in target scope
    $specPath = Join-Path $env:TEMP "replace-spec.txt"
    Set-Content -LiteralPath $specPath -Value ($replaceSpec -join "`n") -Encoding UTF8

    $steps = @(
        'git checkout -b histpurge/docs-only-plan',
        '# optional: ensure clean working tree before proceeding',
        '# dry-run suggestion: operate in a throwaway clone first',
        'git filter-repo --replace-text ' + $specPath + ' --path docs/ --path README.md --path docs/DONELOG.txt --force'
    )

    if ($WhatIf) {
        Write-Host 'Planned commands:' -ForegroundColor Yellow
        $steps | ForEach-Object { Write-Host $_ }
        return
    }

    foreach ($cmd in $steps) {
        if ($cmd.StartsWith('#')) { Write-Host $cmd -ForegroundColor DarkGray; continue }
        Write-Host "> $cmd" -ForegroundColor Green
    Invoke-Expression $cmd
    }

    Write-Host 'Plan applied in current clone. Review the result before pushing.' -ForegroundColor Cyan
    Write-Host 'To push: git push --force-with-lease origin HEAD:main' -ForegroundColor DarkYellow
}
finally {
    Pop-Location
}
