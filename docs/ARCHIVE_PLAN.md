# Archiv-Plan (Phase 2)

Ziel: Vorsichtige Bereinigung klarer Duplikate/Altdateien ohne funktionale Änderungen.

Kandidaten (sicher zu entfernen oder ignorieren):
- eval/eval-21-40_demo_v1.0.json (Duplikat von eval/datasets/eval-21-40_demo_v1.0.json)
- data/system.txt (historisch; aktive Quelle: app/prompt/system.txt)

Vorgehen:
1. Zunächst via .gitignore ausgeschlossen (bereits umgesetzt).
2. Nach Review endgültig löschen (Phase 3) und Referenzen prüfen.

## Phase 4 – Ausführung

- PowerShell (WhatIf/Dry-Run):

  scripts\cleanup_phase4.ps1 -WhatIf:$true

- Ausführen (löscht Dateien):

  scripts\cleanup_phase4.ps1 -WhatIf:$false -Confirm:$true
