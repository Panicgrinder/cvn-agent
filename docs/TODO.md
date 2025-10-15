# CVN Agent – ToDo & Roadmap

Kurzfristige Ziele (Heute)

- [x] Eval-Profile festziehen
  - Ziel: Reproduzierbare Läufe via `eval/config/profiles.json` (quiet default, temp, optionale Checks).
  - Status: Done (UI lädt Profile; Meta-Header vollständig; kurzer ASGI-Lauf konsistent).
- [x] Eval-UI: Profile-/Quiet-/ASGI-/Skip-Preflight-Integration
  - Ziel: Läufe steuerbar über Profile, reduzierte Logs, In-Process-ASGI, Preflight optional.
  - Status: Done (Menü integriert, Flags wirksam, Trends/Exports ok).
- [x] Synonym-Overlay (privat) einführen und mergen
  - Ziel: `eval/config/synonyms.local.json` (gitignored) automatisch mit `synonyms.json` mergen.
  - Status: Done (Loader-Merge, Sample-Datei, Doku in README & eval/README, .gitignore ergänzt).
- [x] Eval-Pfade harmonisieren & Meta-Header erweitern
  - Ziel: Nutzung von `eval/datasets|results|config`, Meta mit overrides (model/host/temperature).
  - Status: Done (Runner/UI angepasst, Ergebnisse validiert).
- [x] Altlasten entfernen
  - Ziel: `app/routers/*`, redundante Prompt-Dateien, alte Helpers entfernen; Doku/Index bereinigen.
  - Status: Done (Bereinigt, Referenzen aktualisiert, Smoke-Eval grün).
- [x] Prompt-Schalter robust machen
  - Ziel: Klare Priorität DEFAULT > UNRESTRICTED > EVAL; saubere Systemprompt-Injektion.
  - Status: Done (Unit-Tests für Default/Unrestricted/Eval hinzugefügt und grün).
- [x] HTTP/Client-Reuse & Timeouts
  - Ziel: Wiederverwendbarer AsyncClient auch im HTTP-Modus + zentrale Timeouts.
  - Status: Done (process_chat_request akzeptiert geteilten AsyncClient; zentraler Timeout bleibt aktiv).
- [x] Unit-Tests: Synonym-Overlay-Merge
  - Ziel: Test, dass `synonyms.local.json` korrekt gemerged wird und fehlende Datei still ignoriert wird.
  - Status: Done (zwei Tests hinzugefügt, beide grün).

- [x] Pyright-Upgrade & Typwarnungen bereinigt
  - Status: Done (Pyright 1.1.406; 0 Fehler, 0 Warnungen; Tests grün; verbleibende Test-Warnungen gefixt)

- [x] Markdownlint-Konfiguration & Tasks
  - Status: Done (`.markdownlint.json` hinzugefügt; VS Code Tasks für Lint/Fix; README/TODO/Customization bereinigt)

1–2 Tage

- [x] Qualitäts-Heuristiken fürs RPG (stilistische Checks)
  - Status: Done (rpg_style-Score + Check; Unit-Tests hinzugefügt; per Checks-Liste aktivierbar)
- [x] Parameter-Sweeps (temperature, top_p, max_tokens)
  - Status: Done (Runner unterstützt Sweeps + Overrides; Tagging/Meta;
    Trends zeigt kompakte Aggregation; top_p end-to-end sichtbar)
- [x] Beobachtbarkeit (Korrelation-ID, JSON-Logs, Trunkierung)
  - Status: Done (Request-ID-Middleware; JSON-Logs für Requests/Errors;
    Trunkierung in Chat-Logs; RID-Weitergabe an Modell; strukturierte Model-Logs)
- [x] Rate-Limits/Schutzschalter Feintuning
  - Status: Done (Fenster/Limit/Burst konfigurierbar; Exempt Paths & Trusted IPs; informative Rate-Limit-Header; Tests grün)
- [x] Streaming-Antworten (optional)
  - Status: Done (POST /chat/stream liefert text/event-stream;
    serverseitige Chunk-Ausgabe via Ollama-Stream; Logs & Fehler-Ereignisse;
    kompatibel zu bestehender /chat API)

- [x] DONELOG-Disziplin auch für Agent-Änderungen
  - Ziel: Sicherstellen, dass direkte Pushes auf `main` ebenfalls einen DONELOG-Eintrag erfordern; bequemer Editor-Flow.
  - Status: Done (CI-Workflow prüft jetzt auch Push auf `main`;
    PR-Bypass via Label bleibt; VS Code Task "Append DONELOG entry" hinzugefügt.)

- [x] Mypy-Enforcement für weitere Skripte ausweiten
  - Ziel: Schrittweises Reduzieren von `[mypy-scripts.*] ignore_errors = True`;
    per Datei auf `check_untyped_defs = True` heben.
  - Kandidaten: `scripts/run_eval.py`, `scripts/eval_ui.py`,
    `scripts/curate_dataset_from_latest.py`, `scripts/openai_finetune.py`,
    `scripts/train_lora.py`.
  - Status: Done — Alle genannten Skripte sind jetzt auf `check_untyped_defs=True`
    gestellt und mypy-clean.

- [ ] Testabdeckung erhöhen (inkrementell)
  - Ziel: Mehr Edge- und Fehlerpfade testen (Streaming-Fehler, Timeout/Rate-Limit, dependency_check-Sonderfälle, Export/Prepare-Interop).
  - Hinweis: Windows-Pfade beachten (keine Laufwerks-Mismatches; projektwurzelnahe Temp-Verzeichnisse nutzen).

- [x] Pre-commit-Hook für DONELOG
  - Ziel: Commit verhindern, wenn Code unter `app/|scripts/|utils/` geändert wurde,
    aber kein aktueller DONELOG-Eintrag vorliegt (Jahres-/Datumscheck).
  - Optional: Interaktiv `scripts/append_done.py` aufrufen.
  - Optional (lokal vorbereitet): `.githooks/pre-commit` + VS Code Tasks
    - Installieren: Task "Git hooks: install local pre-commit"
    - Prüfen: Task "Git hooks: verify pre-commit"
    - Manuell ausführen: Task "Pre-commit: run check"
  - Status: Done (Hook aktiv; erweitert um markdownlint-Prüfung mit Auto-Fix für geänderte .md)

- [x] VS Code Tasks normalisieren (Portabilität)
  - Ziel: Harte `F:/`-Pfade durch `${workspaceFolder}` & `${config:python.interpreterPath}` ersetzen; konsistente CWD-Optionen.
  - Bonus: Tasks für `mypy`, `pyright`, `pytest -q`, `scripts/dependency_check.py` hinzufügen.
  - Status: Done (Tasks portabel; Pyright/Mypy ProblemMatcher; Markdownlint
    Lint/Fix Tasks ergänzt; Windows-Optimierungen für Hook-Tasks und
    Markdownlint-Fallback)

3–7 Tage

- Datensatzkurierung aus Logs (Train/Val-Pack)
  - Status: In Arbeit / Done (Teil 1): Skript `scripts/curate_dataset_from_latest.py` erstellt;
    Export (openai_chat/alpaca), Dedupe & Train/Val-Split;
    VS Code Task "Curate dataset (latest)" hinzugefügt.
- Fine-Tuning/LoRA Mini-Pipeline
- Caching/Memoization für Eval-Reruns
- Rerun-Failed mit Profil/Meta-Rekonstruktion

- [ ] Mini-Eval → Export → Split → LoRA (Smoke)
  - Ziel: 10–20 Items evaluieren (quiet/ASGI), `openai_chat` exportieren, Split erzeugen,
    kurze LoRA-Trainingsprobe (max 10 Steps) mit `--only-free` oder lokalem Modell.
  - Output: Artefakte in `eval/results/finetune/`, Trainingslogs und Metriken festhalten.

- [ ] Eval-Caching & Reruns
  - Ziel: Ergebnis-Caching (z. B. per Key: Prompt+Options), `scripts/rerun_failed.py` integrieren/absichern; Tests für Cache-Hits/Misses.

- [ ] Dedupe/Heuristiken für Trainingsdaten schärfen
  - Ziel: Längenfilter, Near-Duplicate-Checks, optional einfache Qualitätsmetriken vor dem Packen.

- [ ] Dokumentation Training/Feinabstimmung
  - Ziel: README-Abschnitt oder `docs/training.md` mit Minimalbeispiel, Hardware-Hinweisen und Troubleshooting.

Später

- Narrativspeicher (Session Memory)
- Formale Stil-Guidelines + Tests
- Tooling (pre-commit, ruff/black, pins)

- CI/Qualitätstore
  - Ziel: Optionales Coverage-Minimum in CI (z. B. Zeilen/Branches), Linting (ruff/black)
    und Format-Checks per Pre-commit & CI.

- Packaging & Deployability
  - Ziel: Dockerfile/Compose (lokal/offline-freundlich), Healthchecks, Produktionshinweise.

Metriken

- Eval-Erfolgsrate ↑ (gesamt/paketweise)
- Latenz p95 ↓
- 0 RPG-Erkennungen im Eval-Modus; konsistenter RP-Stil im UNRESTRICTED
- Trainingspacks: dedupliziert, ausgewogene Längen
- Logs strukturiert, korrelierbar, ohne sensible Leaks

- Abdeckung: inkrementelle Erhöhung (z. B. +5–10 Prozentpunkte über mehrere Iterationen); Gate optional.

---

Regel: Abgeschlossene Arbeiten dokumentieren (DONELOG)

- Jede nicht-triviale, abgeschlossene Änderung bitte in `docs/DONELOG.txt` erfassen.
- Format je Zeile: `YYYY-MM-DD HH:MM | Author | Kurzbeschreibung` (keine sensiblen Inhalte!).
- Helferskript: `python scripts/append_done.py "Kurzbeschreibung..."` hängt automatisch Zeitstempel und Autor an.
- CI: PRs mit Code-Änderungen (app/, scripts/, utils/) erfordern einen DONELOG-Eintrag; Bypass via Label `skip-donelog` möglich.
- Zusätzlich: Pushes auf `main` werden ebenfalls geprüft. Für Push-Events gibt es keinen
  Label-Bypass. Falls nötig, zuvor `docs/DONELOG.txt` aktualisieren.
- VS Code Task: "Append DONELOG entry" fragt nach einer Kurzbeschreibung und ruft
  `scripts/append_done.py` mit dem aktiven Python-Interpreter auf.
