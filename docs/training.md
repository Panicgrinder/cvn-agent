# Training & Fine-Tuning – Kurzleitfaden

Dieser Leitfaden zeigt den minimalen End‑to‑End‑Ablauf mit vorhandenen Skripten.

## 1) Evaluieren

- Lokal/ASGI (kein Server nötig):
  - Task/Command nutzt `scripts/run_eval.py --asgi --eval-mode --quiet`.
- Optionaler Cache (spart Zeit/Kosten bei Wiederholungen):
  - `--cache` aktiviert `eval/results/cache_eval.jsonl` (Key=messages+options+model+eval_mode).

## 2) Kuratieren/Export

- Neuesten Run exportieren und Train/Val erzeugen:
  - `scripts/curate_dataset_from_latest.py --format openai_chat`
  - Nutzt robustes Mapping (EVAL_FILE_PATTERN=eval-*.json*, source_file in Results)

## 3) Packen (Split/Dedupe)

- `scripts/prepare_finetune_pack.py <export.jsonl> --format openai_chat`
- Optionen:
  - `--min-output-chars 20` (Default)
  - `--no-dedupe` (deaktiviert Instruktions-Dedupe)
  - `--near-dup-threshold 0.8` (optional, Token‑Jaccard auf Instruction)

## 4) Validieren (OpenAI‑Format)

- `scripts/openai_finetune.py <train.jsonl> <val.jsonl> --validate-only`

## 5) LoRA Mini

- `scripts/train_lora.py <train.jsonl> --output outputs/lora-<tag> --max-steps 10`

## Hinweise

- Pfade/Konfiguration: `app/core/settings.py` (Eval‑Dirs, Patterns)
- Synonyme/Checks: `eval/config/{synonyms.json,synonyms.local.json}`
- Doku: `docs/CONTEXT_ARCH.md`, `docs/AGENT_BEHAVIOR.md`, `docs/REPORTS.md`
- Optional: VS‑Code‑Tasks für die Schritte vorhanden.

### Reruns (Profile-aware)

- Skript: `scripts/rerun_from_results.py <results.jsonl>`
- Flags:
  - `--all` (nicht nur Fehlfälle, sondern alle Items erneut ausführen)
  - `--ids eval-foo,eval-bar` (gezielt bestimmte IDs rerunnen)
- Nutzt Meta/Overrides aus der Results-Datei (Profil, Modell, Host, Temperatur, Checks).
- Tipp: Mit `--cache` in `scripts/run_eval.py` lassen sich identische Antworten cachen und teure Aufrufe sparen.
