# CVN Agent - Workspace Datei-Index

## Vollständiger Index aller Dateien im Workspace

### Root-Verzeichnis:
- [`.env`](.env) - Umgebungsvariablen (private Konfiguration)
- [`.env.example`](.env.example) - Template für Umgebungsvariablen
- [`.gitignore`](.gitignore) - Git-Ignorier-Regeln
- [`analysis_chat_routers.md`](analysis_chat_routers.md) - Analyse der Chat-Router
- [`cleanup_recommendations.md`](cleanup_recommendations.md) - Aufräum-Empfehlungen
- [`pyrightconfig.json`](pyrightconfig.json) - Python-Typsystem-Konfiguration
- [`README.md`](README.md) - Projekt-Dokumentation
- [`requirements.txt`](requirements.txt) - Python-Abhängigkeiten
- [`run_server.py`](run_server.py) - Server-Startskript
- [`test_settings.py`](test_settings.py) - Einstellungen-Test
- [`WORKSPACE_INDEX.md`](WORKSPACE_INDEX.md) - Dieser Datei-Index

### .vscode/:
- [`.vscode/extensions.json`](.vscode/extensions.json) - VSCode-Erweiterungsempfehlungen
- [`.vscode/settings.json`](.vscode/settings.json) - Workspace-spezifische Einstellungen
- [`.vscode/tasks.json`](.vscode/tasks.json) - VSCode-Tasks (z. B. Tests)

#### app/:
- [`app/__init__.py`](app/__init__.py) - App-Package-Initialisierung
- [`app/main.py`](app/main.py) - FastAPI Hauptanwendung mit Chat-Endpunkt
- [`app/schemas.py`](app/schemas.py) - Legacy/kompatibel (API nutzt primär `app/api/models.py`)
- [`app/__pycache__/`](app/__pycache__/) - Python-Bytecode-Cache

#### app/api/:
- [`app/api/__init__.py`](app/api/__init__.py) - API-Package-Initialisierung
- [`app/api/chat.py`](app/api/chat.py) - Chat-Request-Processing
- [`app/api/models.py`](app/api/models.py) - API-Datenmodelle (ChatRequest, ChatResponse)
- [`app/api/api.py`](app/api/api.py) - (geparkt) alternative API-Struktur
- [`app/api/chat_helpers.py`](app/api/chat_helpers.py) - (geparkt) Helper-Funktionen
- [`app/api/endpoints/`](app/api/endpoints/) - (geparkt) Endpunktmodule

#### app/core
- [`app/core/__init__.py`](app/core/__init__.py) - Core-Package-Initialisierung
- [`app/core/settings.py`](app/core/settings.py) - Konfigurationseinstellungen
- [`app/core/prompts.py`](app/core/prompts.py) - System-Prompt-Templates

#### app/prompt
- [`app/prompt/system.txt`](app/prompt/system.txt) - System-Prompt (historisch)

#### app/routers (legacy/geparkt)
- [`app/routers/`](app/routers/) - Ältere Router (chat, health, roll, state)

#### app/services
- [`app/services/llm.py`](app/services/llm.py) - LLM-Service (geparkt)

#### app/utils
- [`app/utils/convlog.py`](app/utils/convlog.py) - Konversations-Logging (geparkt)
- [`app/utils/summarize.py`](app/utils/summarize.py) - Zusammenfassungs-Tools (geparkt)
- [`app/utils/examples/`](app/utils/examples/) - Beispiele (geparkt)

### data/:
 - [`data/logs/`](data/logs/) - Laufzeitprotokolle

#### data/logs/:
- [`data/logs/*.jsonl`](data/logs/) - Chat-Protokolle (generiert, gitignored)

### docs/:
- [`docs/customization.md`](docs/customization.md) - Anpassungs-Dokumentation für private Nutzung
- [`docs/TODO.md`](docs/TODO.md) - ToDo & Roadmap für lokale Entwicklungsarbeit

### eval/:
- [`eval/.gitignore`](eval/.gitignore) - Eval-spezifische Git-Ignorier-Regeln

#### eval/datasets/:
- [`eval/datasets/eval-01-20_prompts_v1.0.json`](eval/datasets/eval-01-20_prompts_v1.0.json) - Sachliche Prompts (eval-001 bis eval-020)
- [`eval/datasets/eval-21-40_demo_v1.0.json`](eval/datasets/eval-21-40_demo_v1.0.json) - Demo-/Fantasy-Prompts (eval-021 bis eval-040)
- [`eval/datasets/eval-41-60_dialog_prompts_v1.0.json`](eval/datasets/eval-41-60_dialog_prompts_v1.0.json) - Dialog-Prompts (eval-041 bis eval-060)
- [`eval/datasets/eval-81-100_technik_erklaerungen_v1.0.json`](eval/datasets/eval-81-100_technik_erklaerungen_v1.0.json) - Technische Erklärungen (eval-081 bis eval-100)
- [`eval/datasets/eval-61-80_szenen_prompts_v1.0.json`](eval/datasets/eval-61-80_szenen_prompts_v1.0.json) - Szenen-Prompts (eval-061 bis eval-080)

#### eval/config/:
- [`eval/config/synonyms.json`](eval/config/synonyms.json) - Synonym-Mappings für Evaluierung
- [`eval/config/profiles.json`](eval/config/profiles.json) - Profile/Overrides für Evaluierung
- [`eval/config/synonyms.local.sample.json`](eval/config/synonyms.local.sample.json) - Beispiel für private Synonym-Overlays

#### eval/results/:
- [`eval/results/results_*.jsonl`](eval/results/) - Evaluierungsergebnisse (generiert, gitignored)

#### eval (weitere Dateien):
- [`eval/README.md`](eval/README.md) - Hinweise zu Eval
- [`eval/eval-21-40_demo_v1.0.json`](eval/eval-21-40_demo_v1.0.json) - (historisch) Duplikat außerhalb von datasets/

### examples/:
- [`examples/unrestricted_prompt_example.txt`](examples/unrestricted_prompt_example.txt) - Beispiel für uneingeschränkten Prompt
- [`examples/rpg/models.py`](examples/rpg/models.py) - RPG-Modelle (geparkte Features)
- [`examples/rpg/state.py`](examples/rpg/state.py) - RPG-State-Router (geparkt)
- [`examples/rpg/roll.py`](examples/rpg/roll.py) - RPG-Roll-Router (geparkt)

### scripts/:
- [`scripts/run_eval.py`](scripts/run_eval.py) - Hauptevaluierungsskript
- [`scripts/customize_prompts.py`](scripts/customize_prompts.py) - Tool zur Prompt-Anpassung
- [`scripts/eval_ui.py`](scripts/eval_ui.py) - Interaktive Eval-UI (Trends/Exports)
- [`scripts/export_finetune.py`](scripts/export_finetune.py) - Export Trainingsdaten
- [`scripts/openai_finetune.py`](scripts/openai_finetune.py) - OpenAI Fine-Tune Helper
- [`scripts/openai_ft_status.py`](scripts/openai_ft_status.py) - OpenAI FT Status
- [`scripts/prepare_finetune_pack.py`](scripts/prepare_finetune_pack.py) - Pack-Builder
- [`scripts/quick_eval.py`](scripts/quick_eval.py) - Schnellstart-Eval
- [`scripts/smoke_asgi.py`](scripts/smoke_asgi.py) - ASGI Smoke-Test
- [`scripts/train_lora.py`](scripts/train_lora.py) - LoRA Training (geparkt)
- [`scripts/open_latest_summary.py`](scripts/open_latest_summary.py) - Öffnet die neueste Merged-Zusammenfassung
- [`scripts/open_context_notes.py`](scripts/open_context_notes.py) - Öffnet/legt lokale Kontext-Notizen an
- [`scripts/README.md`](scripts/README.md) - Skriptübersicht

### utils/:
- [`utils/__init__.py`](utils/__init__.py) - Utils-Package-Initialisierung
- [`utils/eval_utils.py`](utils/eval_utils.py) - Evaluierungs-Hilfsfunktionen
- [`utils/message_helpers.py`](utils/message_helpers.py) - Nachrichten-Helfer
- [`utils/context_notes.py`](utils/context_notes.py) - Kontext-Notizen Loader

---

## Datei-Klassifizierung nach Funktion:

### **Konfiguration:**
- [`.env`](.env), [`.env.example`](.env.example)
- [`pyrightconfig.json`](pyrightconfig.json)
- [`requirements.txt`](requirements.txt)
- [`.vscode/extensions.json`](.vscode/extensions.json)
- [`app/core/settings.py`](app/core/settings.py)
- [`app/core/content_rules.json`](app/core/content_rules.json)

### **Dokumentation:**
- [`README.md`](README.md)
- [`analysis_chat_routers.md`](analysis_chat_routers.md)
- [`cleanup_recommendations.md`](cleanup_recommendations.md)
- [`docs/customization.md`](docs/customization.md)
- [`WORKSPACE_INDEX.md`](WORKSPACE_INDEX.md)

### **Hauptanwendung:**
- [`app/main.py`](app/main.py) - FastAPI-Server
- [`app/api/chat.py`](app/api/chat.py) - Chat-Logic
- [`app/api/models.py`](app/api/models.py) - API-Modelle
- [`app/core/prompts.py`](app/core/prompts.py) - Prompt-Management
- [`app/core/content_management.py`](app/core/content_management.py) - Content-Filter
- [`run_server.py`](run_server.py) - Server-Starter

### **Evaluierungssystem:**
- [`eval/datasets/eval-*.json`](eval/datasets/) - Evaluierungs-Datasets
- [`eval/config/synonyms.json`](eval/config/synonyms.json) - Synonym-Datenbank
- [`eval/results/results_*.jsonl`](eval/results/) - Evaluierungsergebnisse

### **Tools & Scripts:**
- [`scripts/customize_prompts.py`](scripts/customize_prompts.py) - Prompt-Anpassungstool
- [`test_settings.py`](test_settings.py) - Einstellungstest

### **Daten & Logs:**
- [`data/system.txt`](data/system.txt) - System-Prompt (historisch)
- [`data/logs/*.jsonl`](data/logs/) - Chat-Protokolle

### **Beispiele:**
- [`examples/unrestricted_prompt_example.txt`](examples/unrestricted_prompt_example.txt) - Prompt-Beispiele

Hinweis: Legacy-Router unter `app/routers/*` sind vorhanden, aktuell geparkt/nicht produktiv eingebunden.

### **Git-Verwaltung:**
- [`.gitignore`](.gitignore) - Haupt-Git-Ignorier-Regeln
- [`eval/.gitignore`](eval/.gitignore) - Eval-spezifische Git-Ignorier-Regeln

---

## Projektstruktur-Übersicht:

```
f:\cvn-agent\
├── app/                    # Hauptanwendung (FastAPI)
│   ├── api/               # API-Endpunkte und Datenmodelle
│   └── core/              # Kernfunktionalität und Konfiguration
├── data/                  # Daten und Logs
│   └── logs/              # Chat-Protokolle
├── docs/                  # Dokumentation
├── eval/                  # Evaluierungssystem und Testdaten
│   ├── datasets/          # Eingabedaten (Prompts)
│   ├── results/           # Ergebnisse (generiert)
│   └── config/            # Konfiguration (z. B. Synonyme)
├── examples/              # Beispiele und Templates
├── scripts/               # Utility-Scripts und Tools
├── utils/                 # Allgemeine Hilfsfunktionen
└── .vscode/               # VSCode-Konfiguration
```

---

**Letzte Aktualisierung:** 2025-08-24
**Projekt:** CVN Agent - Postapokalyptischer Rollenspiel-Chat-Agent
**Zweck:** Vollständiger Überblick über alle Dateien im Workspace

Repository-Hinweis: Standard-Branch ist `main`.