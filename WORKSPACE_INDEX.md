<!-- markdownlint-disable MD013 -->
# CVN Agent - Workspace Datei-Index

Stand: 2025-10-23

## Vollständiger Index aller Dateien im Workspace (aktualisiert)

### Root-Verzeichnis

- [`.coverage`](.coverage) - Coverage-Report (generiert)
- [`.coveragerc`](.coveragerc) - Coverage-Konfiguration
- [`.env`](.env) - Umgebungsvariablen (private Konfiguration)
- [`.env.example`](.env.example) - Template für Umgebungsvariablen
- [`.gitignore`](.gitignore) - Git-Ignorier-Regeln
- [`.markdownlint.json`](.markdownlint.json) - Markdownlint-Konfiguration
- [`coverage.xml`](coverage.xml) - Coverage-Report (XML, generiert)
- [`analysis_chat_routers.md`](analysis_chat_routers.md) - Analyse der Chat-Router
- [`cleanup_recommendations.md`](cleanup_recommendations.md) - Aufräum-Empfehlungen
- [`CONTEXT_ARCH.md`](docs/CONTEXT_ARCH.md) – Kontextfluss Developer ⇄ Copilot ⇄ GPT (Rollen, Beispiele, Privacy)
- [`mypy.ini`](mypy.ini) - mypy-Konfiguration
- [`pyrightconfig.json`](pyrightconfig.json) - Python-Typsystem-Konfiguration
- [`pytest.ini`](pytest.ini) - Pytest-Konfiguration
- [`README.md`](README.md) - Projekt-Dokumentation
- [`LICENSE`](LICENSE) - MIT-Lizenz
- [`requirements.txt`](requirements.txt) - Python-Abhängigkeiten (Laufzeit)
- [`requirements-dev.txt`](requirements-dev.txt) - Dev-Abhängigkeiten (Lint/Tests)
- [`requirements-train.txt`](requirements-train.txt) - Zusatzabhängigkeiten (Training)
- [`run_server.py`](run_server.py) - Server-Startskript
- [`test_settings.py`](test_settings.py) - Einstellungen-Test
- [`WORKSPACE_INDEX.md`](WORKSPACE_INDEX.md) - Dieser Datei-Index
- [`__pycache__/`](__pycache__/) - Python-Bytecode-Cache (generiert)
- [`.mypy_cache/`](.mypy_cache/) - mypy-Cache (generiert)
- [`.pytest_cache/`](.pytest_cache/) - Pytest-Cache (generiert)
- [`.tmp-datasets/`](.tmp-datasets/) - Temporäre Artefakte (generiert)
- [`.tmp-results/`](.tmp-results/) - Temporäre Artefakte (generiert)

### .vscode

- [`.vscode/extensions.json`](.vscode/extensions.json) - VSCode-Erweiterungsempfehlungen
- [`.vscode/launch.json`](.vscode/launch.json) - Startkonfigurationen
- [`.vscode/settings.json`](.vscode/settings.json) - Workspace-spezifische Einstellungen
- [`.vscode/tasks.json`](.vscode/tasks.json) - VSCode-Tasks (z. B. Tests, Eval)
  - Enthält u. a. die Task „Eval: rerun from results“ (profile-aware Reruns aus results_*.jsonl)

### app

- [`app/__init__.py`](app/__init__.py) - App-Package-Initialisierung
- [`app/main.py`](app/main.py) - FastAPI Hauptanwendung mit Chat-/Stream-/Health-Endpunkten
  
Hinweis Datenmodelle: Quelle ist [`app/api/models.py`](app/api/models.py).

#### app/api

- [`app/api/__init__.py`](app/api/__init__.py) - API-Package-Initialisierung
- [`app/api/api.py`](app/api/api.py) - API Router-Bündelung
- [`app/api/chat.py`](app/api/chat.py) - Chat-Request-Processing
- [`app/api/models.py`](app/api/models.py) - API-Datenmodelle
- [`app/api/chat_helpers.py`](app/api/chat_helpers.py) - Legacy/Geparkt (historische Helper)

#### app/core

- [`app/core/__init__.py`](app/core/__init__.py) - Core-Package-Initialisierung
- [`app/core/settings.py`](app/core/settings.py) - Konfigurationseinstellungen
- [`app/core/prompts.py`](app/core/prompts.py) - System-Prompt-Templates (zentral genutzt)
- [`app/core/content_management.py`](app/core/content_management.py) - Inhaltsfilter & Policy-Hooks (optional)
- [`app/core/memory.py`](app/core/memory.py) - Speicher-/Gedächtnis-Funktionen (geparkt)

#### app/prompt

- (entfernt) `app/prompt/system.txt` – Altlast gelöscht; zentrale Quelle ist `app/core/prompts.py`.

#### app/routers (legacy/geparkt)

- [`app/routers/README.md`](app/routers/README.md) - Hinweisdatei (Ordner nicht produktiv eingebunden)

#### app/services

- [`app/services/__init__.py`](app/services/__init__.py) - Services-Package
- [`app/services/llm.py`](app/services/llm.py) - LLM-Service (geparkt)

#### app/utils

- [`app/utils/convlog.py`](app/utils/convlog.py) - Konversations-Logging (geparkt)
- [`app/utils/summarize.py`](app/utils/summarize.py) - Zusammenfassungs-Tools (geparkt)
- [`app/utils/session_memory.py`](app/utils/session_memory.py) - Sitzungsbezogene Speicher-Helfer (geparkt)
- [`app/utils/examples/`](app/utils/examples/) - Beispiele (geparkt)

### utils

- [`utils/__init__.py`](utils/__init__.py) - Utils-Package-Initialisierung
- [`utils/context_notes.py`](utils/context_notes.py) - Lokale Kontext-Notizen laden
- [`utils/eval_utils.py`](utils/eval_utils.py) - Eval-Helfer (truncate, coerce_json_to_jsonl, load_synonyms)
- [`utils/eval_cache.py`](utils/eval_cache.py) - Einfacher JSONL-Cache für LLM-Summaries
- [`utils/message_helpers.py`](utils/message_helpers.py) - Message/Historie Utilities
- [`utils/time_utils.py`](utils/time_utils.py) - Zeit-/Timestamp-Helfer
- [`utils/rag.py`](utils/rag.py) - Leichtgewichtiger TF‑IDF RAG‑Retriever (Index/Save/Load/Retrieve)

### data

- [`data/logs/`](data/logs/) - Laufzeitprotokolle (generiert, gitignored)
  - [`data/logs/*.jsonl`](data/logs/) - Chat-Protokolle

### docs

- [`docs/customization.md`](docs/customization.md) - Anpassungs-Dokumentation für private Nutzung
- [`docs/ARCHIVE_PLAN.md`](docs/ARCHIVE_PLAN.md) - Archiv-/Bereinigungs-Plan (Phasen)
- [`docs/TODO.md`](docs/TODO.md) - ToDo & Roadmap für lokale Entwicklungsarbeit
- [`docs/AGENT_BEHAVIOR.md`](docs/AGENT_BEHAVIOR.md) - System-Prompt, Richtlinien & System-Infos (zentral)
- [`docs/DONELOG.txt`](docs/DONELOG.txt) - DONELOG – Abgeschlossene Arbeiten
  (Hinweis: `AGENT_PROMPT.md` und `BEHAVIOR.md` wurden konsolidiert → `AGENT_BEHAVIOR.md`)
- [`docs/REPORTS.md`](docs/REPORTS.md) - Berichte/Reports Überblick
- [`docs/training.md`](docs/training.md) - Kurzleitfaden Training/Finetuning (inkl. Reruns)
  - Hinweis: Reruns via `scripts/rerun_from_results.py` (Flags: `--all`, `--ids`)
  - Backup/Restore: Separates Backup-Repo mit privaten Releases; MANIFEST (SHA-256) und README mit Restore-Anleitung
- [`docs/reports/`](docs/reports/) - Sammelordner für generierte/kuratierte Reports

### eval

- [`eval/.gitignore`](eval/.gitignore) - Eval-spezifische Git-Ignorier-Regeln
- [`eval/README.md`](eval/README.md) - Hinweise zu Eval
- [`eval/DEPRECATIONS.md`](eval/DEPRECATIONS.md) - Deprecations/Altpfade (Eval)
<!-- Top-Level Duplikat entfernt; maßgeblich sind Dateien unter eval/datasets/ -->

#### eval/datasets

- [`eval/datasets/eval-01-20_prompts_v1.0.json`](eval/datasets/eval-01-20_prompts_v1.0.json) -
  Sachliche Prompts (eval-001 bis eval-020)
- [`eval/datasets/eval-21-40_fantasy_v1.0.json`](eval/datasets/eval-21-40_fantasy_v1.0.json) -
  Fantasy-Prompts (eval-021 bis eval-040)
- [`eval/datasets/eval-41-60_dialog_prompts_v1.0.json`](eval/datasets/eval-41-60_dialog_prompts_v1.0.json)
  - Dialog-Prompts (eval-041 bis eval-060)
- [`eval/datasets/eval-61-80_szenen_prompts_v1.0.json`](eval/datasets/eval-61-80_szenen_prompts_v1.0.json)
  - Szenen-Prompts (eval-061 bis eval-080)
- [`eval/datasets/eval-81-100_technik_erklaerungen_v1.0.json`](eval/datasets/eval-81-100_technik_erklaerungen_v1.0.json)
  - Technische Erklärungen (eval-081 bis eval-100)
- [`eval/datasets/chai-ai_small_v1.jsonl`](eval/datasets/chai-ai_small_v1.jsonl) - Chai-Smalltalk/Empathie-Dataset (aktuell)
- [`eval/datasets/eval-001-100_technik_erklaerungen_v1.0.zip`](eval/datasets/eval-001-100_technik_erklaerungen_v1.0.zip)
  - Archiv (optional)
- [`eval/datasets/combined_eval_001-100.jsonl`](eval/datasets/combined_eval_001-100.jsonl) - Kombiniertes 001-100 JSONL
- [`eval/datasets/eval-101-300_generated_v1.0.jsonl`](eval/datasets/eval-101-300_generated_v1.0.jsonl) - Generierte Zusatzdaten
- [`eval/datasets/eval-smoke.jsonl`](eval/datasets/eval-smoke.jsonl) - Smoke-Test Dataset
- [`eval/datasets/gpt_samples.de.jsonl`](eval/datasets/gpt_samples.de.jsonl) - Beispielantworten (Deutsch)

#### eval/config

- [`eval/config/synonyms.json`](eval/config/synonyms.json) - Synonym-Mappings für Evaluierung
- [`eval/config/profiles.json`](eval/config/profiles.json) - Profile/Overrides für Evaluierung (inkl. „chai“)
- [`eval/config/policy.sample.json`](eval/config/policy.sample.json) - Beispiel-Policy (default + profiles)
- [`eval/config/synonyms.local.json`](eval/config/synonyms.local.json) - Lokales Synonym-Overlay (freundlich/empathisch/einfühlsam/zuwenden)
- [`eval/config/synonyms.local.sample.json`](eval/config/synonyms.local.sample.json) - Beispiel für private Synonym-Overlays
- [`eval/config/context.local.md`](eval/config/context.local.md) - Lokale Kontext-Notizen (privat)
- [`eval/config/context.local.sample.md`](eval/config/context.local.sample.md) - Muster für lokale Kontext-Notizen
- [`eval/config/synonyms.local.sanitized.json`](eval/config/synonyms.local.sanitized.json) - Sanitized/abgeleitete Synonyme

#### eval/results

- [`eval/results/results_*.jsonl`](eval/results/) - Evaluierungsergebnisse (generiert, gitignored)
- Beispiel: `eval/results/results_20251016_0930.jsonl`
- `eval/results/summaries/` - Generierte Workspace-Zusammenfassungen (Map-Reduce/LLM)

### examples

- [`examples/unrestricted_prompt_example.txt`](examples/unrestricted_prompt_example.txt) - Beispiel
  für uneingeschränkten Prompt
- [`examples/rpg/models.py`](examples/rpg/models.py) - RPG-Modelle (geparkte Features)
- [`examples/rpg/state.py`](examples/rpg/state.py) - RPG-State-Router (geparkt)
- [`examples/rpg/roll.py`](examples/rpg/roll.py) - RPG-Roll-Router (geparkt)

### outputs

- [`outputs/`](outputs/) - Generierte Artefakte/Exports (gitignored)
- Beispiel: `outputs/lora-chai-mini-0937/` (LoRA-Adapter & Checkpoints)

### scripts

- [`scripts/README.md`](scripts/README.md) - Hinweise zu Skripten
- [`scripts/run_eval.py`](scripts/run_eval.py) - Hauptevaluierungsskript
- [`scripts/quick_eval.py`](scripts/quick_eval.py) - Schnelle Eval (ASGI)
- [`scripts/eval_ui.py`](scripts/eval_ui.py) - Konsolen-UI für Evaluierung
- [`scripts/eval_loader.py`](scripts/eval_loader.py) - Hilfsfunktionen zum Laden von Evaluationspaketen
- [`scripts/audit_workspace.py`](scripts/audit_workspace.py) - Einfacher Workspace-Audit
- [`scripts/dependency_check.py`](scripts/dependency_check.py) - Konsistenz-/Abhängigkeits-Checks (Eval/Config)
- [`scripts/curate_dataset_from_latest.py`](scripts/curate_dataset_from_latest.py) - Kuratiert Trainingspakete aus results_*.jsonl
- [`scripts/export_finetune.py`](scripts/export_finetune.py) - Exportiert openai_chat aus Eval-Ergebnissen
- [`scripts/prepare_finetune_pack.py`](scripts/prepare_finetune_pack.py) - Train/Val-Pack-Erzeugung aus Export
- [`scripts/openai_finetune.py`](scripts/openai_finetune.py) - Validate-only/Status für OpenAI-Format
- [`scripts/openai_ft_status.py`](scripts/openai_ft_status.py) - Statusabfrage
- [`scripts/train_lora.py`](scripts/train_lora.py) - LoRA-Training (TRL/PEFT)
- [`scripts/fine_tune_pipeline.py`](scripts/fine_tune_pipeline.py) - Mini-Pipeline fürs Fine-Tuning/LoRA
- [`scripts/rerun_from_results.py`](scripts/rerun_from_results.py) - Profile-aware Reruns auf Basis von results_*.jsonl (Flags: --all, --ids)
- [`scripts/rerun_failed.py`](scripts/rerun_failed.py) - Reruns fehlgeschlagener Items
- [`scripts/map_reduce_summary.py`](scripts/map_reduce_summary.py) - Heuristische Workspace-Zusammenfassung
- [`scripts/map_reduce_summary_llm.py`](scripts/map_reduce_summary_llm.py) - LLM-gestützte Zusammenfassung via /chat
- [`scripts/migrate_dataset_schemas.py`](scripts/migrate_dataset_schemas.py) - Migration alter Dataset-Schemata
- [`scripts/customize_prompts.py`](scripts/customize_prompts.py) - Tool zur Prompt-Anpassung
- [`scripts/estimate_tokens.py`](scripts/estimate_tokens.py) - Token-/Größenschätzung
- [`scripts/open_latest_summary.py`](scripts/open_latest_summary.py) - Öffnet neueste Gesamtzusammenfassung
- [`scripts/open_context_notes.py`](scripts/open_context_notes.py) - Öffnet/legt lokale Kontextnotizen an
- [`scripts/append_done.py`](scripts/append_done.py) - Hängt Eintrag an `docs/DONELOG.txt` an
- [`scripts/fix_donelog_times.py`](scripts/fix_donelog_times.py) - Korrigiert Zeitstempel im DONELOG
- [`scripts/cleanup_phase3.ps1`](scripts/cleanup_phase3.ps1) - Cleanup-Skript Phase 3
- [`scripts/cleanup_phase4.ps1`](scripts/cleanup_phase4.ps1) - Cleanup-Skript Phase 4
- [`scripts/history_purge_plan.ps1`](scripts/history_purge_plan.ps1) - Historienbereinigung (Plan)
- [`scripts/run_tests.py`](scripts/run_tests.py) - Test-Launcher/Helper
- [`scripts/smoke_asgi.py`](scripts/smoke_asgi.py) - Minimaler ASGI-Smoketest
- [`scripts/syn_loader.py`](scripts/syn_loader.py) - Loader für Synonym-Overlays
- [`scripts/summarize_eval_results.py`](scripts/summarize_eval_results.py) - Aggregiert Eval-Ergebnisse
- [`scripts/rag_indexer.py`](scripts/rag_indexer.py) - Baut TF‑IDF RAG‑Index aus .md/.txt und speichert JSON

### tests

- [`tests/`](tests/) - Testsuite (Einheiten-/Integrations-Tests)
  - Auszug (nicht vollständig):
    - [`tests/test_chai_checks.py`](tests/test_chai_checks.py) - Tests für Chai-Checks & Synonyme
    - [`tests/test_context_notes.py`](tests/test_context_notes.py)
    - [`tests/test_utils_context_and_summarize.py`](tests/test_utils_context_and_summarize.py)
    - [`tests/test_app_chat_post_happy.py`](tests/test_app_chat_post_happy.py)
    - [`tests/test_streaming_fallback_and_request_id.py`](tests/test_streaming_fallback_and_request_id.py)
    - [`tests/test_prepare_finetune_pack_extras.py`](tests/test_prepare_finetune_pack_extras.py)
    - Weitere Tests siehe Ordnerliste unter `tests/`.

### .github

- [`.github/workflows/`](.github/workflows/) - CI-Workflows (GitHub Actions)

### .githooks (optional)

- [`.githooks/pre-commit`](.githooks/pre-commit) - Lokaler Pre-commit Hook (DONELOG/Lint)

Repository-Hinweis: Standard-Branch ist `main`.

Letzte Aktualisierung: 2025-10-25

Hinweise:

- Prompts: Zentrale Quelle ist [`app/core/prompts.py`](app/core/prompts.py).
  `app/prompt/system.txt` wurde entfernt (Altlast, nicht produktiv genutzt).
- Eval-Daten bitte ausschließlich unter [`eval/datasets/...`](eval/datasets/) pflegen. Zusätzliche
  Dateien im Ordner `eval/` sind dokumentiert.
