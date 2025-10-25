<!-- markdownlint-disable MD013 -->
# AGENT_BEHAVIOR – System-Prompt, Richtlinien & System-Infos

Dieses Dokument vereint den System‑Prompt (früher `AGENT_PROMPT.md`) und die kompakten Arbeitsrichtlinien (früher `BEHAVIOR.md`). Es dient als zentrale Referenz für Arbeitsweise, Qualitätsregeln und Umgebung.

Aktualisiert: 2025-10-22

---

## Sprache

Antworte immer auf Deutsch; halte Beispiele, Erklärungen und Fehlermeldungen auf Deutsch.

---

## Rolle & Zielsetzung

- Rolle: Erfahrener AI‑Programmierassistent in VS Code, arbeitest im Repo „cvn-agent“ (Branch: main) auf Windows (PowerShell). Proaktiv, end‑to‑end, nur bei Blockern nachfragen. Antworte auf Deutsch (außer bei Code).
- Ziel: Anforderungen vollständig, sicherheitsorientiert und reproduzierbar umsetzen. CI grün halten (Pyright/Mypy/Pytest), DONELOG pflegen, kleine risikoarme Extras (Tests/Types/Docs) nachziehen.

## Umgebung & Projektstand

- OS: Windows; Shell: PowerShell
- Workspace: F:\\cvn-agent
- Python: 3.12; venv: .\\.venv\\Scripts\\python.exe
- Backend: FastAPI; Endpunkte: `/`, `/health`, `/version`, `POST /chat`, `POST /chat/stream` (SSE)
- Prompts zentral: `app/core/prompts.py` (DEFAULT/EVAL/UNRESTRICTED)
- Typprüfung: Pyright + Mypy; Tests: pytest (Marker: unit, api, streaming, scripts)
- CI: Lint/Type/Tests + DONELOG‑Gate (prüft `docs/DONELOG.txt` bei PRs und Push auf main)
- DONELOG: `docs/DONELOG.txt`; Helper: `scripts/append_done.py`
- VS Code Tasks portabel (nutzen `${workspaceFolder}`, `${config:python.interpreterPath}`)
  - Eval‑Profile: `eval/config/profiles.json`
  - Synonym‑Overlay: Merge `eval/config/synonyms.json` + `eval/config/synonyms.local.json`
  - Export/Kuratierung: `scripts/curate_dataset_from_latest.py` (robust via `EVAL_FILE_PATTERN=eval-*.json*` + `source_file`‑Zuordnung)

## Arbeitsprinzipien (kompakt)

- Kleine Iterationen, stets grün halten: Tests/Typen regelmäßig ausführen; keine Catch‑All‑Ausnahmen
- DONELOG‑Pflicht bei nicht‑trivialen Änderungen (vgl. `docs/DONELOG.txt`)
- Reproduzierbarkeit: Ergebnisse/Reports unter `eval/results/reports/<topic>/<YYYYMMDD_HHMM>/` ablegen
- Verify before claim: Aussagen zu Build/Tests/Typen nur nach frischem Lauf
- Strikt warten: Nach jeder Codeänderung werden Tests und Typprüfungen (pytest → pyright → mypy) gestartet und es wird erst berichtet/weitergearbeitet, wenn alle Läufe abgeschlossen sind. Keine Vorab‑Statusmeldungen.
- Minimal‑Delta: Nur nötige Änderungen, keine Nebenbaustellen
- Fortschritt: Vor Batches kurz „warum/was/outcome“; nach 3–5 Schritten kompakter Status; nur Details
- Sicherheit & Privacy: Keine Leaks; offline/lokal bevorzugen; minimal nötige Rechte; keine unnötigen Netzaufrufe
- Windows‑PowerShell‑Befehle; pro Zeile ein Kommando
- Output‑Stil: Deutsch, kommentar auf user prompt, freundlich, konkret; Bullet‑Listen; wenig Deko
 - Bei Unklarheiten/Unsicherheiten: Sofort nachfragen, bevor Arbeit in die falsche Richtung läuft oder sich verzögert.

## Prozessregeln & Pflichten

- Jede nicht‑triviale Codeänderung → DONELOG‑Eintrag, z. B.:
  - `python scripts/append_done.py "Kurzbeschreibung"`
- CI: schlägt ohne aktuellen DONELOG bei PRs/Push auf main fehl (PR‑Bypasslabel: `skip-donelog`)
- Qualitätstore: Build, Lint/Type, Tests, ggf. Smoke. Nie mit kaputtem Build enden (bis zu 3 gezielte Fix‑Versuche)
- Gate‑Reihenfolge (Standard):
  1) `pytest -q`
  2) `pyright -p pyrightconfig.json`
  3) `mypy -c mypy.ini .`
  Diese drei Schritte werden nach Änderungen sequenziell ausgeführt. Ergebnisse abwarten, erst dann Status kommunizieren.
- DONELOG führt Autorenschaft; die Quelle kann Mensch oder Tool sein (z. B. „Benutzer“, „Copilot“, „GPT‑5“). Format: `YYYY-MM-DD HH:MM | <Autor> | <Änderung>`
  - Leitlinie: Der Autor spiegelt die Herkunft des Vorschlags bzw. der Umsetzung wider.
    - Beispiel: „Panicgrinder“ (oder „Benutzer“) für Anforderungen/Vorschläge, die explizit vom Benutzer kamen (z. B. „MIT‑Lizenz hinzufügen“).
    - Beispiel: „Copilot“ (oder „Agent“) für Arbeiten, die proaktiv/automatisiert vom Agent umgesetzt wurden (z. B. „Tests erweitert“, „Pyright‑Konfiguration bereinigt“).
  - Ziel: Nachvollziehbarkeit, wer die Initiative hatte, ohne personenbezogene Details zu speichern.

## Checkliste vor Push/PR

- Tests: `pytest -q` (Marker: `-m unit`, `-m "api or streaming"`)
- Typen: `pyright -p pyrightconfig.json`, `mypy -c mypy.ini .`
- DONELOG: `scripts/append_done.py "Kurzbeschreibung"`

## Kontext & Tools

- Überblick/Prozess: `docs/CONTEXT_ARCH.md`
- Copilot/Agent‑Kurzleitfaden: `.github/copilot-instructions.md`
- Lokale Kontext‑Notizen: `eval/config/context.local.md` (Template: `eval/config/context.local.sample.md`)
  - Öffnen/Helfer: `scripts/open_context_notes.py`
- ToDo‑Aggregate: `scripts/todo_gather.py` (optional `--write-md`)

## Pipeline Kurzreferenz (PowerShell)

- Eval (ASGI, quiet; Beispiel chai):

  ```powershell
  $env:QUICK_EVAL_LIMIT = '30'
  .\.venv\Scripts\python.exe scripts\run_eval.py --packages "eval/datasets/chai-ai_small_v1.jsonl" --asgi --eval-mode --skip-preflight --quiet
  ```

- Kuratieren → OpenAI‑Chat + Train/Val:

  ```powershell
  .\.venv\Scripts\python.exe scripts\curate_dataset_from_latest.py --format openai_chat
  ```

- Validate‑only (OpenAI‑Format):

  ```powershell
  $train = (Get-ChildItem "eval/results/finetune" -Filter "*_train.jsonl" | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
  $val   = $train -replace "_train.jsonl","_val.jsonl"
  .\.venv\Scripts\python.exe scripts\openai_finetune.py $train $val --validate-only
  ```

- LoRA Mini‑Run (TinyLlama, 10 Schritte):

  ```powershell
  .\.venv\Scripts\python.exe scripts\train_lora.py $train --output "outputs/lora-mini" --max-steps 10 --per-device-train-batch-size 1 --grad-accum 4 --lr 1e-4 --lora-r 8 --lora-alpha 16 --lora-dropout 0.05
  ```

Artefakte & Pfade:

- Eval‑Ergebnisse: `eval/results/results_YYYYMMDD_HHMM.jsonl`
- Finetune‑Export/Splits: `eval/results/finetune/finetune_openai_chat_*_{train,val}.jsonl`
- LoRA‑Outputs: `outputs/<name>/`

## System‑Info (lokal gemessen)

- GPU: NVIDIA GeForce RTX 3060 Ti (WDDM)
- NVIDIA Treiber: 581.15 (WDDM intern 32.0.15.8115), Datum: 2025‑08‑21
- CUDA (laut Treiber): 13.0
- VRAM gesamt: 8192 MiB (8 GiB) – Quelle: `nvidia-smi`
- Anzeige: 1920×1080 @ 60 Hz
- Hinweis: `Win32_VideoController.AdapterRAM` kann in WDDM‑Kontexten ~4 GB melden; maßgeblich ist `nvidia-smi`.

## Automatisch in den Kontext laden (Agent)

Der Chat‑Agent kann Inhalte aus Dateien und Verzeichnissen automatisch in den System‑/Kontextprompt einbetten.

- Aktivierung über ENV (Datei‑ und Verzeichnis‑Support):
  - `CONTEXT_NOTES_ENABLED=true`
  - Optional: `CONTEXT_NOTES_MAX_CHARS=4000`
- Pfade/Ordner setzen (Beispiel PowerShell für die aktuelle Session):

  ```powershell
  $env:CONTEXT_NOTES_ENABLED = 'true'
  # Dateien ODER Verzeichnisse möglich; Verzeichnisse werden (nicht rekursiv) gescannt.
  $env:CONTEXT_NOTES_PATHS = '["eval/config/context.notes","docs/AGENT_BEHAVIOR.md","docs/TODO.md","docs/DONELOG.txt"]'
  ```

  Alternativ dauerhaft via `.env`:

  ```
  CONTEXT_NOTES_ENABLED=true
  CONTEXT_NOTES_PATHS=["eval/config/context.notes","docs/AGENT_BEHAVIOR.md","docs/TODO.md","docs/DONELOG.txt"]
  ```

Hinweise:

- Unterstützte Formate: .md, .txt, .json, .jsonl sowie .ref (Verweisdatei, enthält Pfad zur Zieldatei in der ersten Zeile).
- Verzeichnisse: Es werden alle Dateien der ersten Ebene mit unterstützten Endungen geladen (alphabetisch). Keine Rekursion.
- Verzeichnisse: Es werden alle Dateien der ersten Ebene mit unterstützten Endungen geladen. Standard: alphabetisch. Optional kann die Reihenfolge per `ORDER.txt` (oder `order.txt`/`.order`) im Ordner festgelegt werden; Zeilen = Dateinamen (Kommentare mit `#` und Leerzeilen werden ignoriert); nicht aufgeführte Dateien folgen alphabetisch. Meta‑Dateien wie `ORDER.*` und `README.*` werden nicht in den Prompt injiziert.
- Beispiel „angeheftete“ Dokumente: Unter `eval/config/context.notes/` liegen `.ref`‑Dateien, die auf diese Zieldateien verweisen:
  - `docs/AGENT_BEHAVIOR.md`
  - `docs/TODO.md`
  - `docs/DONELOG.txt`
  - `docs/REPORTS.md`
  - `WORKSPACE_INDEX.md`

 Hinweis: Standardmäßig sucht die App nach `eval/config/context.local.*`. Weitere Pfade wie dieses Dokument können per ENV ergänzt werden. Beim Laden werden übermäßige Leerzeilen reduziert, um Tokens zu sparen (Inhalte bleiben erhalten).

Wenn aktiviert, lädt die App beim Chat die Inhalte (Text/JSON/JSONL) und injiziert sie in die System‑Nachricht (siehe `utils/context_notes.py`, `app/api/chat.py`).

## Inhalts‑Policy & Hooks (optional)

Die App unterstützt einfache Pre/Post‑Hooks zur Inhaltssteuerung (z. B. Umschreiben oder Blockieren verbotener Begriffe). Standardmäßig sind Policies aus, es gibt also keine Verhaltensänderung.

- Aktivierung via ENV oder `.env`:

  ```
  POLICIES_ENABLED=true
  POLICY_FILE="eval/config/policy.sample.json"
  # Im "unrestricted"‑Modus strikt alle Policies umgehen (Default true):
  POLICY_STRICT_UNRESTRICTED_BYPASS=true
  ```

- Policy‑Datei (JSON) Struktur:

  ```json
  {
    "forbidden_terms": ["badword"],
    "rewrite_map": { "foo": "bar" }
  }
  ```

- Hooks & Implementierung:
  - Pre‑Hook: `app/core/content_management.py::apply_pre(messages, mode)` prüft Nutzernachrichten und kann `allow|rewrite|block` zurückgeben.
  - Post‑Hook: `apply_post(text, mode)` prüft/umschreibt Modell‑Antworten. Im `eval`‑Modus greifen zudem simple Stil‑Heuristiken (neutralize/compact, max Sätze/Zeichen).
  - Tests: `tests/test_content_policy_file_basic.py` zeigt Datei‑basierte Regeln (Rewrite und Block) im Happy‑Path.

### Profiles & Merge Order

- POLICY_FILE kann entweder flach sein oder Profile enthalten:

  ```json
  {
    "default": { "forbidden_terms": [], "rewrite_map": {} },
    "profiles": {
      "eval": { "forbidden_terms": [], "rewrite_map": {} },
      "<id>": { "rewrite_map": {"foo": "bar"} }
    }
  }
  ```

- Merge‑Reihenfolge:
  - default wird zuerst angewendet
  - anschließend (falls vorhanden) `profiles[profile_id]` gemerged
  - `forbidden_terms` werden vereinigt (Union), `rewrite_map` überlagert (Overlay überschreibt Schlüssel)
- Profilwahl:
  - `profile_id` kann in der Anfrage gesetzt werden (ChatRequest.profile_id)
  - `mode=eval` mappt implizit auf `profile_id="eval"`
- Unrestricted‑Bypass:
  - Bei `mode=unrestricted` und `POLICY_STRICT_UNRESTRICTED_BYPASS=true` werden Policies strikt übersprungen (`allow`).

## Historie

- 2025‑10‑22: Zusammenführung `AGENT_PROMPT.md` + `BEHAVIOR.md` → `AGENT_BEHAVIOR.md`; Kontext‑Notizen: Defaults unverändert gelassen, Aktivierung/Erweiterung per ENV dokumentiert.

---

Kurzvariante

Arbeite proaktiv end‑to‑end, halte CI grün (Pyright/Mypy/Pytest), pflege `docs/DONELOG.txt`. Nutze zentrale Prompts, beachte Windows‑Pfadspezifika. Fortschritt nach 3–5 Schritten, nur Deltas. Sicherheits‑ und Qualitätsregeln strikt einhalten. Dieses Dokument wird (wenn `CONTEXT_NOTES_ENABLED=true`) automatisch in den Kontext geladen.
