# CVN Agent
  
[![CI](https://github.com/Panicgrinder/cvn-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Panicgrinder/cvn-agent/actions/workflows/ci.yml)

## Lizenz

Dieses Projekt steht unter der MIT-Lizenz. Siehe die Datei `LICENSE` im Repository-Wurzelverzeichnis.

Ein FastAPI-Backend für einen Conversational Agent, der Ollama als LLM verwendet.

## Neuigkeiten (2025-10-20)

- Demo→Fantasy: Datensatz-Bezeichnungen vereinheitlicht (`eval-21-40_fantasy_v1.0.*`).
   Maßgeblich sind die Dateien unter `eval/datasets/`.
- Reports: Drei Skripte erzeugen reproduzierbare Berichte unter
   `eval/results/reports/<topic>/<timestamp>/`:
   - `scripts/reports/generate_dependencies_report.py`
   - `scripts/reports/generate_coverage_report.py`
   - `scripts/reports/generate_consistency_report.py`
- CI: Ein Workflow erzeugt die Reports automatisch bei Push und lädt sie als
   Artefakte hoch.
- Legacy-Bereinigung: Unbenutzte Legacy-Endpunkte unter `app/api/endpoints/`
   entfernt; doppelte Exporte in `app/services/__init__.py` bereinigt.

## Repository-Info

- Standard-Branch: `main`
- Optional: Zusätzliche Pyright-Konfig für Skripte: `pyrightconfig.scripts.json`

## Einrichtung

1. Python 3.12 installieren
2. Virtuelle Umgebung erstellen und aktivieren:

   ```powershell
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. Abhängigkeiten installieren:

   ```powershell
   pip install -r requirements.txt
   ```
   
   Oder manuell:

   ```bash
   pip install fastapi uvicorn httpx python-dotenv
   ```

4. Ollama installieren und starten:

   ```bash
   # Windows-Installer von https://ollama.com/download/windows
   # Nach der Installation:
   ollama serve
   ```

5. LLM-Modell herunterladen:

   ```powershell
   ollama pull llama3.1:8b
   ```

## Anwendung starten

```bash
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

```text
http://127.0.0.1:8000/docs
```

## Einstellungen/Umgebung

Konfiguration per `.env` (siehe Beispiele in `app/core/settings.py`). Wichtige Felder:


Hinweis: Bei aktiviertem Rate Limiting wird pro IP innerhalb eines 60s-Fensters begrenzt (in-memory, best-effort).

### Policies aktivieren (optional)

Die Inhalts‑Policies sind standardmäßig aus. Zur Aktivierung in `.env` oder Umgebungsvariablen setzen:

```
POLICIES_ENABLED=true
POLICY_FILE="eval/config/policy.sample.json"
# Im "unrestricted"‑Modus strikt alle Policies umgehen:
POLICY_STRICT_UNRESTRICTED_BYPASS=true
```

Hinweise:

- Policy‑Datei kann „default“ und „profiles“ enthalten. Merge‑Reihenfolge: `default` → `profiles[profile_id]`;
   `forbidden_terms` werden vereinigt, `rewrite_map` überlagert die Schlüssel.
- `mode=eval` mappt implizit auf `profile_id="eval"`.
- Details und Tests siehe `docs/AGENT_BEHAVIOR.md` und `tests/test_content_policy_profiles.py`.
 
## Optionale CLI-Tools

Für erweiterte Workflows stehen optionale Skripte zur Verfügung (nicht Teil des API-Pflichtpfads):

- `scripts/customize_prompts.py` – Prompts/Policies/Profiles zusammenstellen; Export in Dateien
- `scripts/estimate_tokens.py` – Grobe Token-/Längenabschätzung für Eingaben
- `scripts/open_context_notes.py` – Kontextnotizen aus `settings` öffnen (lokal)
- `scripts/audit_workspace.py` – Konsistenz-/Altlasten-Scan; Hinweise und Pfadprüfungen
- `scripts/openai_finetune.py` – OpenAI-kompatible Finetune-Packs validieren/Triggern
- `scripts/openai_ft_status.py` – Finetune-Status abfragen
- `scripts/train_lora.py` – LoRA-Miniläufe (TinyLlama etc.)
- `scripts/fine_tune_pipeline.py` – End-to-End Pipeline (Export→Prepare→Train)

Tipps:

- Viele Schritte sind als VS Code Tasks vorhanden (Suche nach „Finetune“, „Eval“, „Summary“).
- Alle Skripte akzeptieren `--help` mit Kurzbeschreibung und Argumenten.
## Datenmodelle (Quelle)

Die zentralen Pydantic-Modelle für Requests/Responses liegen in `app/api/models.py`.
Historische `app/schemas.py` wurde entfernt. Bitte nur `app/api/models.py` importieren.

## Workspace-Zusammenfassung

- Neueste Gesamt-Zusammenfassung (LLM+Heuristik):
   - eval/results/summaries/summary_ALL_20250824_0306_MIXED.md

## Datensatz-Kurierung (3–7 Tage)

Aus Eval-Ergebnissen Trainingspakete erzeugen:

- Skript: `scripts/curate_dataset_from_latest.py`
- Ablauf: nimmt die neueste `results_*.jsonl`, exportiert in `openai_chat` oder `alpaca`, erzeugt deduplizierte Train/Val-Dateien.
- Ausgabe liegt unter `eval/results/finetune/`.

## Finetune workflow

Schneller Export und Vorbereitung von Trainingspaketen auf Basis der neuesten
Evaluations-Ergebnisse (`eval/results/results_*.jsonl`). Zwei VS Code Tasks sind vorhanden:

- Finetune: export (latest)
   - Ermittelt die neueste `results_*.jsonl` und exportiert nach OpenAI-Chat-Format.
   - Ausgabe: `${workspaceFolder}/eval/results/finetune/exports/openai_chat.jsonl`
   - OS-spezifisch (Windows PowerShell vs. Linux/macOS Bash) hinterlegt.

- Finetune: prepare (split)
   - Erzeugt deduplizierte Splits:
      - Train: `${workspaceFolder}/eval/results/finetune/train.jsonl`
      - Val: `${workspaceFolder}/eval/results/finetune/val.jsonl`
   - Schwellwert für Near-Duplicates: `0.92`

Akzeptanz: Das Ausführen beider Tasks erzeugt valide JSONL-Dateien für Train/Val ohne JSON-Fehler.

## Fine-Tuning / LoRA Mini-Pipeline (3–7 Tage)

- Skript: `scripts/fine_tune_pipeline.py`
- Voraussetzungen: passende PyTorch-Installation und optionale Pakete aus `requirements-train.txt`.
- Beispiel (CPU/GPU abhängig):
   - python scripts/fine_tune_pipeline.py \
      --finetune-dir eval/results/finetune \
      --epochs 1 \
      --per-device-train-batch-size 1 \
      --bf16

## Eval: Synonyme mit privatem Overlay

Für die Keyword-Checks in der Evaluierung können Synonyme aus `eval/config/synonyms.json` geladen werden.
Zusätzlich können lokale, private Ergänzungen in
`eval/config/synonyms.local.json` abgelegt werden.
Diese Datei ist git-ignoriert und wird automatisch mit der Basisdatei gemerged.

- Beispiel: `eval/config/synonyms.local.sample.json` kopieren zu `synonyms.local.json` und anpassen.

## Lokale Kontext-Notizen (optional)

Der Server kann optionale, lokale Kontext-Notizen als zusätzliche
System-Nachricht injizieren. Das ist nützlich für projektspezifisches Wissen
oder interne Begriffe.

- Beispieldatei: `eval/config/context.local.sample.md` → kopieren zu `context.local.md` und Inhalte ergänzen.
- Aktivierung via Settings/ENV:
   - `CONTEXT_NOTES_ENABLED=true`
   - Optional Pfade anpassen:
      `CONTEXT_NOTES_PATHS=["eval/config/context.local.md", "eval/config/context.local.jsonl", ...]`
   - Optional Größe begrenzen: `CONTEXT_NOTES_MAX_CHARS=4000`
- Die Notizen werden als zweite System-Nachricht eingefügt (nach dem gewählten
   System-Prompt), sowohl im normalen als auch im Streaming-Endpunkt.
- Fehlende Overlay-Datei wird stillschweigend ignoriert.

## Eval-Style-Guard (Post-Hook im eval_mode)

Der Streaming-Post-Hook normalisiert im `eval_mode` die finale
Assistenten-Antwort heuristisch: neutral, kurz, ohne Rollenspiel/Emoji/
Storytelling. Die Normalisierung greift nur, wenn `eval_mode` aktiv ist und
kann über Settings deaktiviert werden. Der umgeschriebene Text wird in der
Sitzungshistorie persistiert.

- Flags in `app/core/settings.py` (auch per ENV setzbar):
   - `EVAL_POST_REWRITE_ENABLED` (default: `True`)
   - `EVAL_POST_MAX_SENTENCES` (default: `2`)
   - `EVAL_POST_MAX_CHARS` (default: `240`)
   - Heuristiken: Neutralisierung und Kompaktierung
      (Pronomen/Rollenspiel/Emojis/! entfernen, Duplikate/Punktuation
      normalisieren)

- Beispiel: SSE-Tail beim Streaming (eval_mode)

   ```text
   event: delta
   data: {"text":"..."}
   event: meta
   data: {"policy_post":"rewritten","request_id":"<RID>","delta_len":42}
   event: done
   ```

- Eval-Runner Preset: `--profile eval`
   - Setzt konservative Sampling-Defaults (nur wenn nicht manuell
      überschrieben):
      - `temperature=0.2`, `top_p=0.1`, `max_tokens=128`
   - Checks lassen sich fokussieren, z. B.:
      `--checks rpg_style,term_inclusion`
   - Ruhige Ausgabe: `--quiet`

### Schnelle Rezepte (copy/paste)

- CHAI (ASGI, eval-Profil, fokussierte Checks):

   ```bash
   python scripts/run_eval.py --asgi --packages "eval/datasets/chai-ai_small_v1.jsonl" \
      --profile eval --checks rpg_style,term_inclusion --quiet
   ```

- Combined 001–100 (ASGI, eval-Profil, fokussierte Checks):

   ```bash
   python scripts/run_eval.py --asgi --packages "eval/datasets/combined_eval_001-100.jsonl" \
      --profile eval --checks rpg_style,term_inclusion --quiet
   ```

## Copilot @workspace / #codebase (Code-Suche)

- Empfehlung: Remote-Index nutzen (Repo liegt auf GitHub). Lokaler Index dient als Fallback.
- Push regelmäßig, damit der Remote-Index aktuell bleibt.
- Nutzung in Prompts: `@workspace` oder `#codebase` hinzufügen, optional Code markieren/auswählen.
- Status und Index-Build über die Copilot-Statusleiste; bei Bedarf "Build Remote Workspace Index" ausführen.
