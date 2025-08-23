# CVN Agent Evaluierungsskripte

Dieses Verzeichnis enthält Skripte zum Testen und Evaluieren des CVN Agents.

## Skripte

### run_eval.py

Ein Skript zur automatisierten Evaluierung des Chat-Endpunkts:

```
python run_eval.py [prompts_datei] [api_url]
```

Parameter:
- `prompts_datei`: Pfad zur JSONL-Datei mit Testfällen (Standard: `eval/prompts.jsonl`)
- `api_url`: URL des Chat-Endpunkts (Standard: `http://localhost:8000/chat`)

Beispiel:
```
python scripts/run_eval.py eval/prompts.jsonl http://localhost:8000/chat
```

### Abhängigkeiten

Das Skript benötigt die folgenden Python-Pakete:
- httpx
- rich

Installation:
```
pip install httpx rich
```