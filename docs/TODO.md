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

  - Ziel: Mehr Edge- und Fehlerpfade testen (Streaming-Fehler, Timeout/Rate-Limit, dependency_check-Sonderfälle, Export/Prepare-Interop).
  - Hinweis: Windows-Pfade beachten (keine Laufwerks-Mismatches; projektwurzelnahe Temp-Verzeichnisse nutzen).
  - Gruppierung: pytest-Marker eingerichtet (unit, api, streaming, eval, scripts);
    VS Code Tasks für "Tests: unit" und "Tests: api+streaming" hinzugefügt.
  - Fortschritt:
    - Neue Tests für Rate-Limit/Timeout, Prompt-/Options-Parsing, Context-Notes,
      Settings-Validatoren, LLM-Service, Summaries.
    - Skript-Smokes erweitert (neu hinzugefügt):
      - `tests/scripts/test_todo_gather_smoke.py` → scripts/todo_gather.py (jetzt ~88%)
      - `tests/scripts/test_customize_prompts_smoke.py` → scripts/customize_prompts.py (jetzt ~48%)
      - `tests/scripts/test_map_reduce_summary_llm_smoke.py` → scripts/map_reduce_summary_llm.py (jetzt ~62%)
      - `tests/scripts/test_open_latest_summary_smoke.py` → scripts/open_latest_summary.py (Happy-Path, Print)
      - `tests/scripts/test_fine_tune_pipeline_smoke.py` → scripts/fine_tune_pipeline.py (Free‑Modell, --no-check, kurzer Pfad)
    - Ergebnis: Scripts-Zeilenabdeckung zuletzt ~67% (vorher ~60–65%);
      weitere Runden erhöht (letzte Messung 69% mit Branch-Coverage,
      erneute Messung steht an).
    - Zusätzlich: Beispiel‑Test `tests/test_chai_checks.py` prüft `check_term_inclusion`
      inkl. Synonym‑Erkennung.
  - Nächste Schritte:
    - [x] Integrationstest: alpaca Export→Prepare
      - Test: `tests/scripts/test_export_and_prepare_pipeline_alpaca.py` (Export alpaca → Prepare-Pack; Train/Val erzeugt)
    - [x] Weitere Edge-Tests ergänzt (export_finetune, open_context_notes, rerun_failed, fine_tune_pipeline)
    - [x] 3+1 Testrunde (customize_prompts, map_reduce_summary, fine_tune_pipeline + /health Header)
      - Resultat: Suite grün; Scripts-Coverage ~75% (Branch-Coverage aktiv)
    - [x] 3+1 Testrunde (map_reduce_summary Python/JSON, rerun_failed JSON-Array, export_finetune Fallback + /404 Header)
      - Resultat: Suite grün; Scripts-Coverage ~78%
    - [x] 3+1 Testrunde (fine_tune_pipeline fp16/KeyboardInterrupt, export_finetune openai_chat include_failures, /chat/stream Fehler-SSE)
      - Resultat: Suite grün; Scripts-Coverage stabil ~78%
    - [x] 3+1 Testrunde (migrate_dataset_schemas Happy-Path, openai_ft_status Snapshot+Follow, [App-Test bereits enthalten])
      - Resultat: Suite grün; Scripts-Coverage ~79%
    - [x] 3+1 Testrunde (audit_workspace Fallback, curate_dataset_from_latest Minimal, open_context_notes Happy, /chat Fehlerpfad)
      - Resultat: Suite grün; Scripts-Coverage stabil ~79%
    - [x] Scripts-Coverage erneut messen und gezielt ≥80% anstreben
      - Erreicht: 80% (Branch-Coverage aktiv)
      - Neu hinzugefügt:
        - tests/scripts/test_curate_dataset_filters_empty.py (Filter führen zu Exit 5)
        - tests/test_audit_workspace_references.py (scan_text_references findet Referenzen)
        - tests/test_app_root_request_id.py (X-Request-ID Header auf /)
      - Messung: vollständige Suite mit --cov=scripts --cov-branch

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

## Coverage-Ziele & Tasks

- Ziele (vereinbart):
  - App: ≥85% Zeilen, ≥75–80% Branches (inkrementell anziehen)
  - Scripts: ≥60% Zeilen (Basis, später anheben)
  - Kombiniert: Fail-Under=80 (angezogen)
- VS Code Tasks:
  - "Tests: coverage app (≥85%)"
  - "Tests: coverage scripts (≥60%)"
  - "Tests: coverage (fail-under)" (kombiniert, 80)
  
Hinweise:

- Branch-Coverage ist in `.coveragerc` aktiviert; schwere/interactive Skripte sind ausgeschlossen.
- Zielwerte werden sukzessive angehoben, sobald Teilbereiche stabil darüber liegen.

3–7 Tage

- Datensatzkurierung aus Logs (Train/Val-Pack)
  - Status: In Arbeit / Done (Teil 1): Skript `scripts/curate_dataset_from_latest.py` erstellt;
    Export (openai_chat/alpaca), Dedupe & Train/Val-Split;
    VS Code Task "Curate dataset (latest)" hinzugefügt.
  - Robustheit: Export/Kuratierung verbessert
    - `app/core/settings.py`: `EVAL_FILE_PATTERN` auf `eval-*.json*` erweitert (unterstützt .json und .jsonl).
    - `scripts/export_finetune.py`: nutzt zusätzlich `source_file` aus den Results,
      um Dataset‑Items zuverlässig zuzuordnen (auch wenn Dateien nicht mit `eval-*` benannt sind).
- Fine-Tuning/LoRA Mini-Pipeline
- Caching/Memoization für Eval-Reruns
- Rerun-Failed mit Profil/Meta-Rekonstruktion
  - Status: Done (Basis)
    - `scripts/rerun_from_results.py` rekonstruiert Model/Host/Temperature/Checks aus Meta
    - ASGI/HTTP unterstützt
    - Smoke-Test vorhanden

- [x] Mini-Eval → Export → Split → LoRA (Smoke)
  - Ziel: 10–20 Items evaluieren (quiet/ASGI), `openai_chat` exportieren, Split erzeugen,
    kurze LoRA-Trainingsprobe (max 10 Steps) mit `--only-free` oder lokalem Modell.
  - Output: Artefakte in `eval/results/finetune/`, Trainingslogs und Metriken festhalten.
  - Status: Done (chai-Profil)
    - Eval: 15 Items (ASGI/quiet) aus `eval/datasets/chai-ai_small_v1.jsonl` → `eval/results/results_20251016_0930.jsonl`
    - Kuratierung: `openai_chat` Export + Split → Train (13) / Val (2)
    - Validation: `scripts/openai_finetune.py ... --validate-only` → VALIDATION_OK
    - LoRA Mini: 10 Schritte (TinyLlama), Output: `outputs/lora-chai-mini-0937/`
    - Begleitende Verbesserungen: Checks vereinfacht; Synonyms‑Overlay erweitert; Test `tests/test_chai_checks.py` hinzugefügt.

- [x] Eval-Caching (Basis)
  - Status: Done — Optional per `--cache`
    - Speichert Antworten in `eval/results/cache_eval.jsonl`
    - Key: messages+options+model+eval_mode
    - Reruns folgen separat

- [x] Dedupe/Heuristiken für Trainingsdaten schärfen (Basis)
  - Status: Done — `prepare_finetune_pack.py` unterstützt `--near-dup-threshold` (Token‑Jaccard) zusätzlich zur Instruktions‑Dedupe.

- [x] Dokumentation Training/Feinabstimmung
  - Status: Done — `docs/training.md` (Minimalablauf, Optionen, Hinweise).

Neu (Backups & Releases)

- [x] Backup-Repo (Release-Assets) erstellen und initial befüllen
  - Status: Done — Neues GitHub-Repo erstellt; `main` enthält README+MANIFEST; kompletter
    Snapshot als Release-Assets hochgeladen (ZIPs, gesplittete .venv-Parts). LFS-Grenzen
    damit umgangen.
- [x] Checksums & Restore-Doku ergänzen
  - Status: Done — Backup-Repo: MANIFEST mit SHA-256 für alle Assets erzeugt; README
    um Restore-Anleitung (Parts zusammenfügen, Verifikation) ergänzt.
  - Hinweis: Optional Verschlüsselung (7‑Zip AES‑256) für sensible Artefakte vorbereiten.

Kurz-Update (2025-10-20)

- [x] Reruns vereinheitlicht (Profile-aware)
  - Skript: [`scripts/rerun_from_results.py`](scripts/rerun_from_results.py)
  - Task: VS Code „Eval: rerun from results“
- [x] Checksums & Restore
  - Skript: [`scripts/generate_checksums.py`](scripts/generate_checksums.py)
  - Doku: [`docs/RESTORE.md`](docs/RESTORE.md)
- [x] Workspace-Index/Tasks konsolidiert
  - Datei: [`WORKSPACE_INDEX.md`](WORKSPACE_INDEX.md)
  - Tasks: normalisiert

Offene Punkte (Kurzfristig)

- [ ] Integrationstest „alpaca Export→Prepare“
  - Ziel: End-to-End (Results → Export alpaca → Prepare-Pack)
  - Status: Offen (Testdatei fehlt). Anknüpfen an vorhandene Tests: [`tests/scripts/test_export_finetune_more_edges.py`](tests/scripts/test_export_finetune_more_edges.py), [`tests/test_prepare_finetune_pack_nodedupe.py`](tests/test_prepare_finetune_pack_nodedupe.py)
- [ ] Cleanup: harte Laufwerks-Pfade entfernen
  - Datei: [`scripts/cleanup_phase3.ps1`](scripts/cleanup_phase3.ps1) nutzt absolute F:\-Pfade → relativ/`${workspaceFolder}` umstellen
- [ ] Doku-Drift bereinigen
  - [`cleanup_recommendations.md`](cleanup_recommendations.md) meldet entfernten Chat-Endpunkt; tatsächlich aktiv in [`app/main.py`](app/main.py)

Neu: Reports-Standard

- [x] Bericht-Ordner festlegen
  - Struktur: `eval/results/reports/<topic>/<YYYYMMDD_HHMM>/`
  - Inhalte pro Run:
    - `report.md` (Ergebnisse)
    - `params.txt` (Testparameter/Scope)
  - Vorteil: reproduzierbare Audits; klare Trennung von Artefakten

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
