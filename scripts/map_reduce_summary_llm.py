#!/usr/bin/env python
"""
LLM-gestützter Map-Reduce Summarizer für den Workspace.

Verwendung (empfohlen im ASGI-In-Process-Modus, kein laufender Server nötig):
  python scripts/map_reduce_summary_llm.py --asgi --out-dir eval/results/summaries \
      --llm-scopes app,scripts,utils,tests,docs --heuristic-scopes eval-datasets \
      --max-files 0 --max-chars 700 --concurrency 4 --num-predict 220 --temperature 0.2

Standard: LLM für Code/Doku; Heuristik für große Datensätze. Ergebnisse als Markdown pro Scope
plus eine gemergte Gesamtdatei. Request-IDs werden pro Datei gesetzt.
"""
from __future__ import annotations

import os
import sys
import json
import argparse
import asyncio
from utils.time_utils import now_compact
from typing import List, Dict, Any, Tuple, Optional, TYPE_CHECKING, Protocol, cast
"""Cache/Key Utilities (robust gegen fehlende utils.eval_cache)."""
# Cache für LLM-Summaries (EvalCache dynamisch geladen in _get_llm_cache)
try:
    from utils.eval_cache import make_key
except Exception:
    def make_key(obj: Any) -> str:  # fallback
        import hashlib, json as _json
        return hashlib.sha256(_json.dumps(obj, sort_keys=True, default=str).encode("utf-8")).hexdigest()
class _EvalCacheProto(Protocol):
    def get(self, key: str) -> Optional[str]:
        ...
    def put(self, key: str, value: str) -> None:
        ...

_LLM_CACHE: Optional[_EvalCacheProto] = None
def _get_llm_cache() -> Optional[_EvalCacheProto]:
    global _LLM_CACHE
    if _LLM_CACHE is None:
        try:
            from utils.eval_cache import EvalCache as _EvalCacheCls
            _LLM_CACHE = cast(_EvalCacheProto, _EvalCacheCls(os.path.join(PROJECT_ROOT, "eval", "results", "cache_llm.jsonl")))
        except Exception:
            _LLM_CACHE = None
    return _LLM_CACHE

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

DEFAULT_OUT_DIR = os.path.join(PROJECT_ROOT, "eval", "results", "summaries")

SCOPES = {
    "app": os.path.join(PROJECT_ROOT, "app"),
    "scripts": os.path.join(PROJECT_ROOT, "scripts"),
    "utils": os.path.join(PROJECT_ROOT, "utils"),
    "tests": os.path.join(PROJECT_ROOT, "tests"),
    "docs": os.path.join(PROJECT_ROOT, "docs"),
    "eval-datasets": os.path.join(PROJECT_ROOT, "eval", "datasets"),
}

EXCLUDE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".git", ".venv", "venv", "node_modules", "results"}
TEXT_EXTS = {".py", ".md", ".txt", ".json", ".jsonl"}

# Import Settings und Heuristik-Fallback
from app.core.settings import settings
try:
    from scripts.map_reduce_summary import summarize_file as heuristic_summarize_file
except Exception:
    heuristic_summarize_file = None  # type: ignore[assignment]


def is_text_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in TEXT_EXTS


def safe_read(path: str, max_bytes: Optional[int] = None) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read() if max_bytes is None else f.read(max_bytes)
    except Exception:
        return ""


def collect_files(scope_dir: str, max_files: int = 0) -> List[str]:
    files: List[str] = []
    for root, dirnames, filenames in os.walk(scope_dir):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
        for fn in sorted(filenames):
            fp = os.path.join(root, fn)
            if not is_text_file(fp):
                continue
            files.append(fp)
            if max_files and len(files) >= max_files:
                return files
    return files


def build_summary_prompt(rel_path: str, content: str) -> List[Dict[str, str]]:
    system = (
        "Du bist ein präziser Code- und Doku-Summarizer. Antworte kurz, strukturiert, in Markdown. "
        "Liste wichtige Komponenten/APIs, Abhängigkeiten, Konfig-Punkte, Risiken und TODOs.")
    user = (
        f"Erstelle eine kompakte Zusammenfassung dieser Datei: {rel_path}\n\n"
        "Formatvorgabe:\n"
        "- Zweck & Kontext (1–2 Sätze)\n"
        "- Wichtige Klassen/Funktionen oder Abschnitte\n"
        "- Konfiguration/Parameter\n"
        "- Risiken/Edge-Cases\n"
        "- TODO/Follow-ups (falls erkennbar)\n\n"
        "Dateiinhalt (gekürzt):\n" + content)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


if TYPE_CHECKING:
    import httpx


async def llm_summarize_file(
    client: "httpx.AsyncClient",
    api_url: str,
    path: str,
    run_id: str,
    max_chars: int,
    num_predict: int,
    temperature: float,
) -> str:
    rel = os.path.relpath(path, PROJECT_ROOT)
    # begrenze Inputgröße (große Dateien werden gekürzt)
    content = safe_read(path, max_bytes=256*1024)
    if len(content) > max_chars:
        content = content[:max_chars] + "\n... (gekürzt)"
    messages = build_summary_prompt(rel, content)
    payload: Dict[str, Any] = {
        "messages": messages,
        # eigenes Systemprompt ist gesetzt → kein eval/unrestricted nötig
        "options": {
            "temperature": float(temperature),
            "num_predict": int(num_predict),
        },
    }
    # Cache-Hit prüfen
    cache = _get_llm_cache()
    if cache is not None:
        cache_key = make_key({"rel": rel, "api": api_url, "options": payload["options"], "messages": messages})
        cached: Optional[str] = cache.get(cache_key)
        if isinstance(cached, str) and cached:
            return cached
    headers = {"Content-Type": "application/json", settings.REQUEST_ID_HEADER: f"{run_id}-{rel}"}
    resp = await client.post(api_url, json=payload, headers=headers)
    resp.raise_for_status()
    data_any = resp.json()
    # sichere Typisierung
    from typing import cast as _cast
    data: Dict[str, Any]
    if isinstance(data_any, dict):
        data = _cast(Dict[str, Any], data_any)
    else:
        data = {}
    try:
        summary = data.get("content") or data.get("message", {}).get("content") or ""
        # Cache schreiben
        if cache is not None and summary:
            cache_key2 = make_key({"rel": rel, "api": api_url, "options": payload["options"], "messages": messages})
            cache.put(cache_key2, summary)
        return summary
    except Exception:
        # Fehler werden im Aufrufer abgefangen und dort per Heuristik gefallbackt
        raise


async def process_scope(
    scope: str,
    scope_dir: str,
    use_llm: bool,
    api_url: str,
    asgi: bool,
    run_id: str,
    max_files: int,
    max_chars: int,
    num_predict: int,
    temperature: float,
    concurrency: int,
) -> List[str]:
    import httpx
    files = collect_files(scope_dir, max_files=max_files)
    if not files:
        return []

    summaries: List[str] = []

    if use_llm:
        # Client vorbereiten (ASGI/HTTP)
        if asgi:
            from app.main import app as fastapi_app
            transport = httpx.ASGITransport(app=fastapi_app)
            client = httpx.AsyncClient(transport=transport, base_url="http://asgi", timeout=60.0)
            url = "/chat"
        else:
            client = httpx.AsyncClient(timeout=60.0)
            url = f"{settings.OLLAMA_HOST.rstrip('/')}/chat"

        sem = asyncio.Semaphore(max(1, concurrency))

        async def _one(p: str) -> None:
            nonlocal summaries
            async with sem:
                try:
                    s: str = await llm_summarize_file(client, url, p, run_id, max_chars, num_predict, temperature)
                except Exception as e:
                    # Fallback auf Heuristik
                    if heuristic_summarize_file is not None:
                        s = str(heuristic_summarize_file(p, max_chars=max_chars))
                    else:
                        s = f"Datei: {os.path.relpath(p, PROJECT_ROOT)}\nFehler: {e}"
                summaries.append(s)

        try:
            await asyncio.gather(*[_one(p) for p in files])
        finally:
            await client.aclose()
    else:
        # Nur Heuristik
        for p in files:
            try:
                if heuristic_summarize_file is not None:
                    summaries.append(heuristic_summarize_file(p, max_chars=max_chars))
                else:
                    # Minimaler Fallback
                    rel = os.path.relpath(p, PROJECT_ROOT)
                    txt = safe_read(p, max_bytes=max_chars)
                    summaries.append(f"Datei: {rel}\n\n{txt}")
            except Exception as e:
                summaries.append(f"Datei: {os.path.relpath(p, PROJECT_ROOT)}\nFehler: {e}")

    return summaries


def write_md(out_path: str, title: str, sections: List[Tuple[str, List[str]]]) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        for heading, paras in sections:
            f.write(f"## {heading}\n\n")
            for p in paras:
                f.write(p)
                f.write("\n\n")


async def amain(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    # --llm-scopes darf optional ohne Wert übergeben werden (wird dann als leer interpretiert)
    ap.add_argument("--llm-scopes", type=str, nargs="?", const="", default="app,scripts,utils,tests,docs")
    ap.add_argument("--heuristic-scopes", type=str, default="eval-datasets")
    ap.add_argument("--asgi", action="store_true", help="ASGI In-Process statt HTTP")
    ap.add_argument("--out-dir", type=str, default=DEFAULT_OUT_DIR)
    ap.add_argument("--max-files", type=int, default=0)
    ap.add_argument("--max-chars", type=int, default=700)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--num-predict", type=int, default=220)
    ap.add_argument("--temperature", type=float, default=0.2)
    args = ap.parse_args(argv)

    timestamp = now_compact()
    run_id = f"summary-{timestamp}"

    # leere Angabe ("--llm-scopes" ohne Wert) ergibt eine leere Liste → nur Heuristik verwenden
    llm_scopes = [s.strip() for s in (args.llm_scopes or "").split(",") if s.strip()]
    h_scopes = [s.strip() for s in args.heuristic_scopes.split(",") if s.strip()]

    produced: List[str] = []
    merged_sections: List[Tuple[str, List[str]]] = []

    for scope in llm_scopes + h_scopes:
        scope_dir = SCOPES.get(scope)
        if not scope_dir or not os.path.isdir(scope_dir):
            continue
        use_llm = scope in llm_scopes
        summaries = await process_scope(
            scope=scope,
            scope_dir=scope_dir,
            use_llm=use_llm,
            api_url=f"{settings.OLLAMA_HOST.rstrip('/')}/chat",
            asgi=args.asgi,
            run_id=run_id,
            max_files=args.max_files,
            max_chars=args.max_chars,
            num_predict=args.num_predict,
            temperature=args.temperature,
            concurrency=args.concurrency,
        )
        if not summaries:
            continue
        out_path = os.path.join(args.out_dir, f"summary_{timestamp}_{scope}_llm.md" if use_llm else f"summary_{timestamp}_{scope}_heuristic.md")
        title = f"Workspace Zusammenfassung – {scope} ({'LLM' if use_llm else 'Heuristik'})"
        write_md(out_path, title, [("Dateien", summaries)])
        produced.append(out_path)
        merged_sections.append((f"{scope} ({'LLM' if use_llm else 'Heuristik'})", summaries[: min(50, len(summaries))]))

    if produced:
        merged_path = os.path.join(args.out_dir, f"summary_ALL_{timestamp}_MIXED.md")
        write_md(merged_path, "Workspace Zusammenfassung – Gesamt (LLM+Heuristik)", merged_sections)
        print(json.dumps({
            "timestamp": timestamp,
            "run_id": run_id,
            "asgi": args.asgi,
            "out_dir": args.out_dir,
            "produced": produced,
            "merged": merged_path,
        }, ensure_ascii=False, indent=2))
        return 0
    else:
        print(json.dumps({"error": "Keine Scopes verarbeitet"}, ensure_ascii=False))
        return 1


def main() -> int:
    return asyncio.run(amain())


if __name__ == "__main__":
    sys.exit(main())
