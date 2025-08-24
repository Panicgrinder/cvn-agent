# CVN Agent

Ein FastAPI-Backend für einen Conversational Agent, der Ollama als LLM verwendet.

## Repository-Info

- Standard-Branch: `main`

## Einrichtung

1. Python 3.12 installieren
2. Virtuelle Umgebung erstellen und aktivieren:
   ```
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```
3. Abhängigkeiten installieren:
   ```
   pip install -r requirements.txt
   ```
   Oder manuell:
   ```
   pip install fastapi uvicorn httpx python-dotenv
   ```
4. Ollama installieren und starten:
   ```
   # Windows-Installer von https://ollama.com/download/windows
   # Nach der Installation:
   ollama serve
   ```
5. LLM-Modell herunterladen:
   ```
   ollama pull llama3.1:8b
   ```

## Anwendung starten

```
uvicorn app.main:app --reload
```

## API-Endpunkte

- `GET /`: Basis-Endpunkt für Gesundheitsprüfung
- `POST /chat`: Chat-Endpunkt zum Senden von Nachrichten an das LLM

### Chat-Endpunkt verwenden

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"messages\":[{\"role\":\"user\",\"content\":\"Du bist die Chronistin. Stell dich kurz vor.\"}]}"
```

Oder mit PowerShell:
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" -Method Post -Body '{"messages":[{"role":"user","content":"Du bist die Chronistin. Stell dich kurz vor."}]}' -ContentType "application/json"
```

## Swagger-Dokumentation

Zugriff auf die API-Dokumentation unter:
```
http://127.0.0.1:8000/docs

## Einstellungen/Umgebung

Konfiguration per `.env` (siehe Beispiele in `app/core/settings.py`). Wichtige Felder:

- OLLAMA_HOST, MODEL_NAME, TEMPERATURE
- BACKEND_CORS_ORIGINS: JSON- oder Komma-Liste
- REQUEST_TIMEOUT (Sek.), REQUEST_MAX_INPUT_CHARS, REQUEST_MAX_TOKENS
- RATE_LIMIT_ENABLED (bool), RATE_LIMIT_REQUESTS_PER_MINUTE, RATE_LIMIT_BURST

Hinweis: Bei aktiviertem Rate Limiting wird pro IP innerhalb eines 60s-Fensters begrenzt (in-memory, best-effort).
```

## Workspace-Zusammenfassung

- Neueste Gesamt-Zusammenfassung (LLM+Heuristik):
   - eval/results/summaries/summary_ALL_20250824_0306_MIXED.md

Helfer zum Öffnen der neuesten Zusammenfassung:

- Skript: `scripts/open_latest_summary.py`
- Funktion: Findet die neueste Datei vom Muster `summary_ALL_*_MIXED.md` unter `eval/results/summaries` und öffnet sie mit dem Standardprogramm.

## Datensatz-Kurierung (3–7 Tage)

Aus Eval-Ergebnissen Trainingspakete erzeugen:

- Skript: `scripts/curate_dataset_from_latest.py`
- Ablauf: nimmt die neueste `results_*.jsonl`, exportiert in `openai_chat` oder `alpaca`, erzeugt deduplizierte Train/Val-Dateien.
- Ausgabe liegt unter `eval/results/finetune/`.

## Fine-Tuning / LoRA Mini-Pipeline (3–7 Tage)

- Skript: `scripts/fine_tune_pipeline.py`
- Voraussetzungen: passende PyTorch-Installation und optionale Pakete aus `requirements-train.txt`.
- Beispiel (CPU/GPU abhängig):
   - python scripts/fine_tune_pipeline.py --finetune-dir eval/results/finetune --epochs 1 --per-device-train-batch-size 1 --bf16

## Eval: Synonyme mit privatem Overlay

Für die Keyword-Checks in der Evaluierung können Synonyme aus `eval/config/synonyms.json` geladen werden.
Zusätzlich können lokale, private Ergänzungen in `eval/config/synonyms.local.json` abgelegt werden. Diese Datei ist git-ignoriert und wird automatisch mit der Basisdatei gemerged.

- Beispiel: `eval/config/synonyms.local.sample.json` kopieren zu `synonyms.local.json` und anpassen.

## Lokale Kontext-Notizen (optional)

Der Server kann optionale, lokale Kontext-Notizen als zusätzliche System-Nachricht injizieren. Das ist nützlich für projektspezifisches Wissen oder interne Begriffe.

- Beispieldatei: `eval/config/context.local.sample.md` → kopieren zu `context.local.md` und Inhalte ergänzen.
- Aktivierung via Settings/ENV:
   - `CONTEXT_NOTES_ENABLED=true`
   - Optional Pfade anpassen: `CONTEXT_NOTES_PATHS=["eval/config/context.local.md", "eval/config/context.local.jsonl", ...]`
   - Optional Größe begrenzen: `CONTEXT_NOTES_MAX_CHARS=4000`
- Die Notizen werden als zweite System-Nachricht eingefügt (nach dem gewählten System-Prompt), sowohl im normalen als auch im Streaming-Endpunkt.
- Fehlende Overlay-Datei wird stillschweigend ignoriert.