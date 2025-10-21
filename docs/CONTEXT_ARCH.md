# Kontext-Architektur: Developer × Copilot × Prompt Assistant

Dieses Dokument beschreibt, wie die Zusammenarbeit zwischen dir (Developer), GitHub Copilot (lokal im Editor) und dem GPT‑basierten Copilot Prompt Assistant (Chat) funktioniert. Ziel: effizienter Fluss von Idee → Code → Review → PR – mit klarem Scope und Datenschutz.

## Überblick (Kontextfluss)

```text
[Developer]
   │  formuliert Aufgaben, priorisiert, bewertet
   ▼
[Prompt Assistant (GPT)]  — ToDo/DONE, Vorschläge, Reviews, Doku‑Snippets
   │        ▲
   │        │ nutzt Kontext aus: @workspace, @terminal, @github (mit Zustimmung)
   ▼        │
[GitHub Copilot (VS Code)] — Inline‑Completions, Edits, PR/Issues‑Integration
   │        ▲
   │        │ lokale Dateien, Tests, Terminal, Git
   ▼        │
[Code/Repo] — Build/Lint/Tests → PR → CI
```

- Der Developer bleibt Entscheider: startet Aktionen, nimmt Patches an, merged PRs.
- Prompt Assistant orchestriert Aufgaben (kleine ToDos, Reviews, Docs, Befehle), ohne Secrets zu persistieren.
- Copilot liefert schnelle Code‑Vorschläge und Editor‑Automatisierung.

## Rollen & Fähigkeiten

- Developer
  - Ziele setzen, Anforderungen klären, Entscheidungen treffen
  - Patches/PRs prüfen und mergen, heikle Änderungen freigeben
  - Sensible Daten schützen (keine Tokens/Secrets in Chats)

- GitHub Copilot (VS Code)
  - Inline‑Completions, Multi‑Line Edits, Quick Fixes
  - PR/Issues‑Workflows, Code‑Navigation (@workspace), Terminal‑Kontext (@terminal)
  - Lokale Tests/Linting anstoßen; CI‑Checks im Editor einsehen

- GPT‑basierter Prompt Assistant
  - Aufgaben gliedern, ToDo/DONE pflegen, Aktionsvorschläge machen
  - Code‑/Test‑Reviews, Doku‑Bausteine, Migrations‑/Refactor‑Pläne
  - Kontext‑Zusammenführung: @workspace (Dateien), @terminal (Ausgaben), @github (PRs), nur mit Zustimmung

## Typischer Ablauf (Prompt → Code → Review → PR)

1) Prompt/Anforderung
- Developer beschreibt Ziel (z. B. „Chai‑Checks vereinfachen“).
- Assistant konkretisiert ToDos, schlägt Tests/Scope vor.

1) Code‑Änderung
- Copilot generiert/ergänzt Code (z. B. Tests, Skript‑Refactor), Assistant liefert Begleittexte/Begründungen.

1) Verifikation
- Lokale Tests/Lint/Typecheck (Assistant kann Tasks/Kommandos vorschlagen; Developer führt aus oder autorisiert).

1) Review & PR
- Assistant erzeugt PR‑Beschreibung/CHANGELOG‑Hinweise.
- Developer prüft/merged. CI läuft in GitHub Actions.

## Privacy & Scope

- Keine Secrets/Tokens in Chats posten oder in Repo schreiben.
- Der Assistant liest nur Dateien/Terminal/PR‑Daten, wenn du es erlaubst.
- Lokale Artefakte (.venv, logs, outputs) werden nicht geteilt; reiner Arbeitskontext genügt.
- Minimale Offenlegung: nur benötigte Ausschnitte/Fehlermeldungen verwenden.

## Kontext-Booster: @workspace, @terminal, @github

- @workspace
  - „Zeig alle Verwendungen von check_term_inclusion in `scripts/run_eval.py`.“
  - „Finde Dubletten in `eval/config/synonyms*.json` und schlage Merge vor.“

- @terminal
  - „Erkläre den letzten pytest‑Fehler und schlage Fix‑Patch vor.“
  - „Fasse die Ausgaben von `openai_finetune.py --validate-only` kurz zusammen.“

- @github
  - „Liste offene PRs, die `eval/` oder `scripts/*eval*` ändern.“
  - „Erzeuge eine prägnante PR‑Beschreibung aus den letzten Commits.“

## Quick Tips für neue Teammitglieder

- Halte Aufgaben klein (≤ 30 Minuten), damit Vorschläge zielgenau bleiben.
- Öffne relevante Dateien im Editor, bevor du Fragen stellst (besserer Kontext).
- Nutze Copilot für Code, den Assistant für Planung/Reviews/Doku.
- Bevor du pusht: Tests lokal laufen lassen; PR erst erstellen, wenn grün.

## Reports & Artefakte

- Standard für Berichte: siehe `docs/REPORTS.md`.
- Automatisierte Reports (Dependencies/Coverage/Konsistenz) werden unter `eval/results/reports/<topic>/<timestamp>` abgelegt und per CI als Artefakte hochgeladen.
