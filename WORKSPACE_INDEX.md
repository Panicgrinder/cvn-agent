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

### app/:
- [`app/__init__.py`](app/__init__.py) - App-Package-Initialisierung
- [`app/main.py`](app/main.py) - FastAPI Hauptanwendung mit Chat-Endpunkt
- [`app/schemas.py`](app/schemas.py) - Pydantic-Schemas
- [`app/__pycache__/`](app/__pycache__/) - Python-Bytecode-Cache

#### app/api/:
- [`app/api/__init__.py`](app/api/__init__.py) - API-Package-Initialisierung
- [`app/api/chat.py`](app/api/chat.py) - Chat-Request-Processing
- [`app/api/models.py`](app/api/models.py) - API-Datenmodelle (ChatRequest, ChatResponse)

#### app/core/:
- [`app/core/__init__.py`](app/core/__init__.py) - Core-Package-Initialisierung
- [`app/core/settings.py`](app/core/settings.py) - Konfigurationseinstellungen
- [`app/core/content_management.py`](app/core/content_management.py) - Content-Filter-Management
- [`app/core/prompts.py`](app/core/prompts.py) - System-Prompt-Templates
- [`app/core/content_rules.json`](app/core/content_rules.json) - Benutzerdefinierte Inhaltsregeln

### data/:
- [`data/system.txt`](data/system.txt) - System-Prompt-Datei

#### data/logs/:
- [`data/logs/*.jsonl`](data/logs/) - Chat-Protokolle (generiert, gitignored)

### docs/:
- [`docs/customization.md`](docs/customization.md) - Anpassungs-Dokumentation für private Nutzung

### eval/:
- [`eval/.gitignore`](eval/.gitignore) - Eval-spezifische Git-Ignorier-Regeln
- [`eval/eval-01-20_prompts_v1.0.json`](eval/eval-01-20_prompts_v1.0.json) - Sachliche Prompts (eval-001 bis eval-020)
- [`eval/eval-21-40_demo_v1.0.json`](eval/eval-21-40_demo_v1.0.json) - Demo-/Fantasy-Prompts (eval-021 bis eval-040)
- [`eval/eval-41-60_dialog_prompts_v1.0.json`](eval/eval-41-60_dialog_prompts_v1.0.json) - Dialog-Prompts (eval-041 bis eval-060)
- [`eval/eval-81-100_technik_erklaerungen_v1.0.json`](eval/eval-81-100_technik_erklaerungen_v1.0.json) - Technische Erklärungen (eval-081 bis eval-100)
- [`eval/synonyms.json`](eval/synonyms.json) - Synonym-Mappings für Evaluierung
- [`eval/results_*.jsonl`](eval/) - Evaluierungsergebnisse (generiert, gitignored)

### examples/:
- [`examples/unrestricted_prompt_example.txt`](examples/unrestricted_prompt_example.txt) - Beispiel für uneingeschränkten Prompt

### scripts/:
- [`scripts/run_eval.py`](scripts/run_eval.py) - Hauptevaluierungsskript
- [`scripts/customize_prompts.py`](scripts/customize_prompts.py) - Tool zur Prompt-Anpassung

### utils/:
- [`utils/__init__.py`](utils/__init__.py) - Utils-Package-Initialisierung
- [`utils/eval_utils.py`](utils/eval_utils.py) - Evaluierungs-Hilfsfunktionen

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
- [`scripts/run_eval.py`](scripts/run_eval.py) - Evaluierungs-Engine
- [`utils/eval_utils.py`](utils/eval_utils.py) - Evaluierungs-Utilities
- [`eval/eval-*.json`](eval/) - Evaluierungs-Datasets
- [`eval/synonyms.json`](eval/synonyms.json) - Synonym-Datenbank
- [`eval/results_*.jsonl`](eval/) - Evaluierungsergebnisse

### **Tools & Scripts:**
- [`scripts/customize_prompts.py`](scripts/customize_prompts.py) - Prompt-Anpassungstool
- [`test_settings.py`](test_settings.py) - Einstellungstest

### **Daten & Logs:**
- [`data/system.txt`](data/system.txt) - System-Prompt
- [`data/logs/*.jsonl`](data/logs/) - Chat-Protokolle

### **Beispiele:**
- [`examples/unrestricted_prompt_example.txt`](examples/unrestricted_prompt_example.txt) - Prompt-Beispiele

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
├── examples/              # Beispiele und Templates
├── scripts/               # Utility-Scripts und Tools
├── utils/                 # Allgemeine Hilfsfunktionen
└── .vscode/               # VSCode-Konfiguration
```

---

**Letzte Aktualisierung:** 2025-08-23
**Projekt:** CVN Agent - Postapokalyptischer Rollenspiel-Chat-Agent
**Zweck:** Vollständiger Überblick über alle Dateien im Workspace