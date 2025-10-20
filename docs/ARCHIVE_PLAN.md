# Archiv-Plan (Phase 2)

Ziel: Vorsichtige Bereinigung klarer Duplikate/Altdateien ohne funktionale Änderungen.

Kandidaten (sicher zu entfernen oder ignorieren):

- eval/eval-21-40_fantasy_v1.0.* (Duplikate vermeiden; echte Quelle liegt unter eval/datasets/eval-21-40_fantasy_v1.0.json)
- data/system.txt (historisch; zentrale Quelle ist app/core/prompts.py; `app/prompt/system.txt` nur optionales Template)

Vorgehen:

1. Zunächst via .gitignore ausgeschlossen (bereits umgesetzt).
2. Nach Review endgültig löschen (Phase 3) und Referenzen prüfen.

Aktueller Status (2025-10-16):

- `eval/eval-21-40_demo_v1.0.json`: Historisch; wird nicht mehr genutzt und bleibt ignoriert.
- `data/system.txt`: Derzeit nicht im Repo vorhanden; zusätzlich per `.gitignore` ignoriert.
- Zentrale Prompt-Quelle: `app/core/prompts.py` (vorhanden); optionales Template: `app/prompt/system.txt` (leer, optional).

Prüfkommandos (PowerShell):

```powershell
Get-ChildItem -Path "eval" -Filter "eval-21-40_fantasy_v1.0.*" -Recurse
Test-Path "data/system.txt"
Select-String -Path .gitignore -SimpleMatch "eval/eval-21-40_demo_v1.0.json","eval/eval-21-40_fantasy_v1.0.*","data/system.txt"
```

## Phase 4 – Ausführung

- PowerShell (WhatIf/Dry-Run):

  scripts\cleanup_phase4.ps1 -WhatIf:$true

- Ausführen (löscht Dateien):

  scripts\cleanup_phase4.ps1 -WhatIf:$false -Confirm:$true
