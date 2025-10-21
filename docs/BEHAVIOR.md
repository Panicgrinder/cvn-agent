# Projektverhalten & Arbeitsrichtlinien

Ziel: Konsistente Zusammenarbeit, klarer Kontext und reproduzierbare Ergebnisse – kurz und praxisnah.

## Kernprinzipien

- Kleine Iterationen, stets grün halten:
  - Tests (pytest) und Typen (pyright/mypy) regelmäßig ausführen.
  - Linting für Docs/Code beachten, keine Catch-All-Ausnahmen.
- DONELOG-Pflicht bei nicht-trivialen Änderungen (vgl. `docs/DONELOG.txt`).
- Reproduzierbarkeit: Ergebnisse als kurze Reports/Artefakte ablegen (siehe `docs/REPORTS.md`).
- „Verify before claim“: Erst prüfen, dann behaupten. Aussagen zu Build/Tests/Typen nur mit frischem Lauf.
- Minimal-Delta: Nur das Nötigste ändern, keine Nebenbaustellen aufmachen.

## Kontext & Rollen

- Überblick/Prozess: `docs/CONTEXT_ARCH.md`
- Prompt-/Agent-Richtlinien: `docs/AGENT_PROMPT.md`
- Copilot/Agent-Kurzleitfaden: `.github/copilot-instructions.md`

## Arbeitskontext aktuell halten

- Lokale Kontext-Notizen (privat, nicht eingecheckt): `eval/config/context.local.md`
  - Template: `eval/config/context.local.sample.md`
  - Öffnen/Helfer: `scripts/open_context_notes.py`
- ToDo-/Status-Aggregate: `scripts/todo_gather.py` (optional `--write-md`)

## Berichte/Artefakte

- Standard: `docs/REPORTS.md`
- Zielordner: `eval/results/reports/<topic>/<YYYYMMDD_HHMM>/`
  - Inhalte: `report.md`, `params.txt`, optional `data.json`

## Checkliste vor Push/PR

- Tests: `pytest -q` (Marker bei Bedarf: `-m "api or streaming"`, `-m unit`)
- Typen: `pyright -p pyrightconfig.json`, `mypy -c mypy.ini .`
- DONELOG: Eintrag via `scripts/append_done.py "Kurzbeschreibung"`

## Kommunikationsregeln (knapp)

- Sprache konsequent nach Vorgabe (Standard: Deutsch, außer anders gewünscht).
- Unklare Punkte: maximal 1 gezielte Rückfrage; wenn riskant, Annahmen explizit markieren.
- Fortschritt melden: kurz, mit Fakten (PASS/FAIL, Commit-ID), kein Overhead.

Letzte Aktualisierung: 2025-10-21
