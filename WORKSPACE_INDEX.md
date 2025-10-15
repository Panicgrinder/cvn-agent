# CVN Agent - Workspace Datei-Index

## Vollständiger Index aller Dateien im Workspace

### Root-Verzeichnis

- [`.coverage`](.coverage) - Coverage-Report (generiert)
- [`pytest.ini`](pytest.ini) - Pytest-Konfiguration
- [`.env`](.env) - Umgebungsvariablen (private Konfiguration)
- [`.env.example`](.env.example) - Template für Umgebungsvariablen
- [`.gitignore`](.gitignore) - Git-Ignorier-Regeln
- [`analysis_chat_routers.md`](analysis_chat_routers.md) - Analyse der Chat-Router
- [`cleanup_recommendations.md`](cleanup_recommendations.md) - Aufräum-Empfehlungen
- [`pyrightconfig.json`](pyrightconfig.json) - Python-Typsystem-Konfiguration
- [`mypy.ini`](mypy.ini) - mypy-Konfiguration
- [`README.md`](README.md) - Projekt-Dokumentation
- [`requirements.txt`](requirements.txt) - Python-Abhängigkeiten (Laufzeit)
- [`requirements-dev.txt`](requirements-dev.txt) - Dev-Abhängigkeiten (Lint/Tests)
- [`requirements-train.txt`](requirements-train.txt) - Zusatzabhängigkeiten (Training)
- [`run_server.py`](run_server.py) - Server-Startskript
- [`test_settings.py`](test_settings.py) - Einstellungen-Test
- [`WORKSPACE_INDEX.md`](WORKSPACE_INDEX.md) - Dieser Datei-Index
- [`__pycache__/`](__pycache__/) - Python-Bytecode-Cache (generiert)
- [`.pytest_cache/`](.pytest_cache/) - Pytest-Cache (generiert)

### .vscode

- [`.vscode/extensions.json`](.vscode/extensions.json) - VSCode-Erweiterungsempfehlungen
- [`.vscode/launch.json`](.vscode/launch.json) - Startkonfigurationen
- [`.vscode/settings.json`](.vscode/settings.json) - Workspace-spezifische Einstellungen
- [`.vscode/tasks.json`](.vscode/tasks.json) - VSCode-Tasks (z. B. Tests, Eval)

### app

- [`app/__init__.py`](app/__init__.py) - App-Package-Initialisierung
- [`app/main.py`](app/main.py) - FastAPI Hauptanwendung mit Chat-/Stream-/Health-Endpunkten
  
Hinweis Datenmodelle: Quelle ist [`app/api/models.py`](app/api/models.py).

#### app/api

- [`app/api/__init__.py`](app/api/__init__.py) - API-Package-Initialisierung
- [`app/api/chat.py`](app/api/chat.py) - Chat-Request-Processing (aktiv)
- [`app/api/models.py`](app/api/models.py) - API-Datenmodelle (Quelle)
- [`app/api/chat_helpers.py`](app/api/chat_helpers.py) - Legacy/Geparkt (historische Helper)
- [`app/api/endpoints/README.md`](app/api/endpoints/README.md) - Legacy/Geparkt (historische Endpunktmodule, nicht produktiv)

#### app/core

- [`app/core/__init__.py`](app/core/__init__.py) - Core-Package-Initialisierung
- [`app/core/settings.py`](app/core/settings.py) - Konfigurationseinstellungen
- [`app/core/prompts.py`](app/core/prompts.py) - System-Prompt-Templates (zentral genutzt)
- [`app/core/content_management.py`](app/core/content_management.py) - Inhaltsfilter (optional/geparkt)

#### app/prompt

- [`app/prompt/system.txt`](app/prompt/system.txt) - Optionales Template (nicht produktiv referenziert; zentrale Quelle ist `app/core/prompts.py`)

#### app/routers (entfernt)

- `app/routers/` wurde entfernt (Duplikate zu main/api). Verbleibende Stub-Dateien wurden bereinigt.

#### app/services

- [`app/services/llm.py`](app/services/llm.py) - LLM-Service (geparkt)

#### app/utils

- [`app/utils/convlog.py`](app/utils/convlog.py) - Konversations-Logging (geparkt)
- [`app/utils/summarize.py`](app/utils/summarize.py) - Zusammenfassungs-Tools (geparkt)
- [`app/utils/examples/`](app/utils/examples/) - Beispiele (geparkt)

### utils

- [`utils/context_notes.py`](utils/context_notes.py) - Lokale Kontext-Notizen laden
- [`utils/eval_utils.py`](utils/eval_utils.py) - Eval-Helfer (truncate, coerce_json_to_jsonl, load_synonyms)
- [`utils/eval_cache.py`](utils/eval_cache.py) - Einfacher JSONL-Cache für LLM-Summaries

### data

- [`data/logs/`](data/logs/) - Laufzeitprotokolle (generiert, gitignored)
  - [`data/logs/*.jsonl`](data/logs/) - Chat-Protokolle

### docs

- [`docs/customization.md`](docs/customization.md) - Anpassungs-Dokumentation für private Nutzung
- [`docs/ARCHIVE_PLAN.md`](docs/ARCHIVE_PLAN.md) - Archiv-/Bereinigungs-Plan (Phasen)
- [`docs/TODO.md`](docs/TODO.md) - ToDo & Roadmap für lokale Entwicklungsarbeit

### eval

- [`eval/.gitignore`](eval/.gitignore) - Eval-spezifische Git-Ignorier-Regeln
- [`eval/README.md`](eval/README.md) - Hinweise zu Eval
- [`eval/DEPRECATIONS.md`](eval/DEPRECATIONS.md) - Deprecations/Altpfade (Eval)

#### eval/datasets

- [`eval/datasets/eval-01-20_prompts_v1.0.json`](eval/datasets/eval-01-20_prompts_v1.0.json) - Sachliche Prompts (eval-001 bis eval-020)
- [`eval/datasets/eval-21-40_demo_v1.0.json`](eval/datasets/eval-21-40_demo_v1.0.json) - Demo-/Fantasy-Prompts (eval-021 bis eval-040)
- [`eval/datasets/eval-41-60_dialog_prompts_v1.0.json`](eval/datasets/eval-41-60_dialog_prompts_v1.0.json) - Dialog-Prompts (eval-041 bis eval-060)
- [`eval/datasets/eval-61-80_szenen_prompts_v1.0.json`](eval/datasets/eval-61-80_szenen_prompts_v1.0.json) - Szenen-Prompts (eval-061 bis eval-080)
- [`eval/datasets/eval-81-100_technik_erklaerungen_v1.0.json`](eval/datasets/eval-81-100_technik_erklaerungen_v1.0.json) - Technische Erklärungen (eval-081 bis eval-100)

#### eval/config

- [`eval/config/synonyms.json`](eval/config/synonyms.json) - Synonym-Mappings für Evaluierung
- [`eval/config/profiles.json`](eval/config/profiles.json) - Profile/Overrides für Evaluierung
- [`eval/config/synonyms.local.sample.json`](eval/config/synonyms.local.sample.json) - Beispiel für private Synonym-Overlays
- [`eval/config/context.local.sample.md`](eval/config/context.local.sample.md) - Muster für lokale Kontext-Notizen

#### eval/results

- [`eval/results/results_*.jsonl`](eval/results/) - Evaluierungsergebnisse (generiert, gitignored)
- `eval/results/summaries/` - Generierte Workspace-Zusammenfassungen (Map-Reduce)

#### eval (weitere Dateien)

- (keine; Duplikate außerhalb von `datasets/` wurden entfernt)

### examples

- [`examples/unrestricted_prompt_example.txt`](examples/unrestricted_prompt_example.txt) - Beispiel für uneingeschränkten Prompt
- [`examples/rpg/models.py`](examples/rpg/models.py) - RPG-Modelle (geparkte Features)
- [`examples/rpg/state.py`](examples/rpg/state.py) - RPG-State-Router (geparkt)
- [`examples/rpg/roll.py`](examples/rpg/roll.py) - RPG-Roll-Router (geparkt)

### outputs

- [`outputs/`](outputs/) - Generierte Artefakte/Exports (gitignored)

### scripts

- [`scripts/README.md`](scripts/README.md) - Hinweise zu Skripten
- [`scripts/run_eval.py`](scripts/run_eval.py) - Hauptevaluierungsskript
- [`scripts/eval_ui.py`](scripts/eval_ui.py) - Konsolen-UI für Evaluierung
- [`scripts/audit_workspace.py`](scripts/audit_workspace.py) - Einfacher Workspace-Audit
- [`scripts/dependency_check.py`](scripts/dependency_check.py) - Konsistenz-/Abhängigkeits-Checks (Eval/Config)
- [`scripts/quick_eval.py`](scripts/quick_eval.py) - Schnelle Eval (ASGI, wenige Items)
- [`scripts/map_reduce_summary.py`](scripts/map_reduce_summary.py) - Heuristische Workspace-Zusammenfassung
- [`scripts/map_reduce_summary_llm.py`](scripts/map_reduce_summary_llm.py) - LLM-gestützte Zusammenfassung via /chat
- [`scripts/curate_dataset_from_latest.py`](scripts/curate_dataset_from_latest.py) - Kuratiert Trainingspakete aus der neuesten results_*.jsonl
- [`scripts/rerun_failed.py`](scripts/rerun_failed.py) - Erzeugt JSONL mit fehlgeschlagenen Items zur gezielten Wiederholung
- [`scripts/todo_gather.py`](scripts/todo_gather.py) - Sammelt Metriken/Status für TODO-Überblick und erzeugt optional Markdown-Bericht
- [`scripts/migrate_dataset_schemas.py`](scripts/migrate_dataset_schemas.py) - Migration alter Dataset-Schemata
- [`scripts/customize_prompts.py`](scripts/customize_prompts.py) - Tool zur Prompt-Anpassung
- [`scripts/fine_tune_pipeline.py`](scripts/fine_tune_pipeline.py) - Mini-Pipeline fürs Fine-Tuning/LoRA
- [`scripts/cleanup_phase4.ps1`](scripts/cleanup_phase4.ps1) - Phase‑4 Cleanup-Skript (WhatIf/Confirm)

### tests

- [`tests/`](tests/) - Testsuite (Einheiten-/Integrations-Tests)

### .github

- [`.github/workflows/`](.github/workflows/) - CI-Workflows (GitHub Actions)

Repository-Hinweis: Standard-Branch ist `main`.

Letzte Aktualisierung: 2025-10-15

Hinweise:

- Prompts: Zentrale Quelle ist [`app/core/prompts.py`](app/core/prompts.py). `app/prompt/system.txt` ist nur ein optionales Template und wird im Code nicht geladen.
- Eval-Duplikate wurden entfernt; bitte ausschließlich [`eval/datasets/...`](eval/datasets/) verwenden.
