## Kurz-Anleitung für AI-Coding-Agenten (cvn-agent)

Arbeitskontext
- Repo: `cvn-agent` (Branch: `main`). Backend: FastAPI + Ollama. Schlüsseldateien: `app/main.py`, `app/api/models.py`, `app/core/settings.py`, `app/core/prompts.py`.

Schnellziele (bei Codeänderungen)
- CI grün halten: Tests (pytest), Typen (Pyright/Mypy). CI prüft DONELOG (`docs/DONELOG.txt`).
- Nicht-triviale Änderungen → DONELOG via `scripts/append_done.py`.
- Nach jedem Edit: Tests/Typen sequenziell ausführen und abwarten (Standard: `pytest -q` → `pyright -p pyrightconfig.json` → `mypy -c mypy.ini .`). Keine Vorab-Statusmeldungen.

PR-Checkliste (kurz)
- Tests lokal: `pytest -q` (oder Teilmengen, siehe Marker unten).
- Typechecks: `pyright -p pyrightconfig.json`, `mypy -c mypy.ini .` (Tasks vorhanden).
- Optional: Task „Tests: coverage (fail-under)“ (Gate 80%).
- Wenn `app/`, `scripts/`, `utils/` geändert → DONELOG aktualisieren (Push auf main erfordert Eintrag; PR-Bypass per Label `skip-donelog`).

Pytest-Marker & Teil-Läufe
- Unit: `pytest -q -m unit`
- API/Streaming: `pytest -q -m "api or streaming"`
- Selektiv: `pytest -q -k test_rate_limit_headers_on_success`

API & Integration
- Endpunkte: `/`, `/health`, `/version`, `POST /chat`, `POST /chat/stream` (SSE).
- Prompts zentral (`app/core/prompts.py`); lokale Kontext-Notizen via ENV (`CONTEXT_NOTES_ENABLED=true`, Pfade in `settings`).
- Synonyme: Basis `eval/config/synonyms.json`, Overlay `eval/config/synonyms.local.json` (optional, gemerged).

Konventionen (wichtig)
- Modelle immer aus `app/api/models.py` importieren (nicht `app/schemas.py`).
- Request-ID-Header `X-Request-ID` wird von Middleware gesetzt – auch bei Fehlern (HTTPException-Header werden gemerged).
- Rate-Limit ist ENV-gesteuert; Tests reloaden Module nach `monkeypatch.setenv(...)`.

Häufige Fehlerquellen (kurz)
- Streaming (SSE): Generator muss Events liefern; Tests erwarten u. a. `event: meta` mit `"policy_post"`, `event: delta` mit `"text"`, und `event: done`.
- Rate-Limit-Header: Wenn Limiter aktiv ist, bei Erfolg `X-RateLimit-{Limit,Remaining,Window}` setzen; 429 enthält zusätzlich `Retry-After`.
- CORS-ENV: `BACKEND_CORS_ORIGINS` erlaubt JSON-Liste oder Komma-Liste (siehe Validator in `settings`).

Workflows & Artefakte
- Start lokal: `uvicorn app.main:app --reload` (Swagger: `/docs`).
- Finetune-Export/Prepare: Tasks „Finetune: export (latest)“ → `scripts/export_finetune.py`, „Finetune: prepare (split)“ → `scripts/prepare_finetune_pack.py` (Outputs unter `eval/results/finetune/`).

Wo nachsehen
- CI/Workflows: `.github/workflows/ci.yml`, `.github/workflows/enforce-donelog.yml`.
- Tests: `tests/` (z. B. `test_app_*` für Health/Request-ID/Rate-Limit; Streaming-/Policy-Tests geben Formatvorgaben vor).
- Skripte: `scripts/` (Eval/Export/Train/Reports) – nutze vorhandene CLI-Optionen.

Wenn bereits vorhanden
- Beim Aktualisieren dieser Datei: Inhalte aus `docs/AGENT_BEHAVIOR.md` beachten (Progress-Cadence, DONELOG, Shell-Hinweise) und konsistent halten.
	- Zusätzlich: „Warten bis Checks abgeschlossen sind“ strikt beherzigen und im Zweifelsfall den VS Code Task „All checks: tests+pyright+mypy“ nutzen.

Feedback
- Fehlt dir etwas (weitere Marker, Tasks, Troubleshooting)? Kurz melden – ich passe die Anleitung an.
