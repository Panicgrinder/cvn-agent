# CVN Agent Evaluierungsskripte

Dieses Verzeichnis enthält Skripte zum Testen und Evaluieren des CVN Agents.

## Skripte

### run_eval.py

Ein Skript zur automatisierten Evaluierung des Chat-Endpunkts:

```
python run_eval.py [prompts_datei] [api_url]
```

Parameter:
 - openai_finetune.py – OpenAI-Fine-Tuning anstoßen
- `prompts_datei`: Pfad zur JSON/JSONL-Datei mit Testfällen (Standard: `eval/datasets/eval-*.json`)
- `api_url`: URL des Chat-Endpunkts (Standard: `http://localhost:8000/chat`)

Beispiel:
```
 - OpenAI FT: openai_finetune.py
	 - Voraussetzungen: `pip install openai`; `OPENAI_API_KEY` gesetzt
	 - Datensätze: openai_chat `*_train.jsonl` und `*_val.jsonl`
	 - Aufruf: `python scripts/openai_finetune.py eval/datasets/xxx_train.jsonl eval/datasets/xxx_val.jsonl --model gpt-4o-mini`
	python scripts/run_eval.py --packages eval/datasets/eval-*.json http://localhost:8000/chat
```

### Abhängigkeiten

Das Skript benötigt die folgenden Python-Pakete:
- httpx
- rich

Installation:
```
pip install httpx rich
```