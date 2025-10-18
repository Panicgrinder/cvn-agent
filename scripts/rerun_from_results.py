#!/usr/bin/env python
"""
Profile-aware Reruns aus einer bestehenden results_*.jsonl.

Funktionen:
- Liest Meta-Header aus der Results-Datei (enabled_checks, eval_mode, asgi, overrides, api_url, patterns)
- Rekonstruiert Laufparameter (Model/Host/Temperature/TopP/NumPredict/Retries)
- Lädt passende Items (über Meta.patterns oder Fallback-Globs) und führt nur 
  gewünschte IDs erneut aus (fehlgeschlagene, alle oder explizite Liste)
- Schreibt neue results_*_rerun.jsonl mit kopiertem Meta (+rerun_from)

Beispiel:
  python scripts/rerun_from_results.py eval/results/results_20251016_0930.jsonl
  python scripts/rerun_from_results.py eval/results/results_20251016_0930.jsonl --all
  python scripts/rerun_from_results.py eval/results/results_20251016_0930.jsonl --ids eval-foo,eval-bar
"""
from __future__ import annotations

import os
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, cast


def _load_module_run_eval():
    import sys, importlib.util
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    run_eval_path = os.path.join(project_root, "scripts", "run_eval.py")
    spec = importlib.util.spec_from_file_location("run_eval", run_eval_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Konnte run_eval.py nicht laden")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


run_eval = _load_module_run_eval()


def _load_results_with_meta(path: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    meta: Dict[str, Any] = {}
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            if i == 0 and isinstance(obj, dict) and obj.get("_meta"):
                meta = cast(Dict[str, Any], obj)
            else:
                rows.append(cast(Dict[str, Any], obj))
    return meta, rows


async def rerun_from_results(
    results_path: str,
    only_failed: bool = True,
    ids: Optional[List[str]] = None,
) -> Dict[str, Any]:
    import httpx

    meta, rows = _load_results_with_meta(results_path)
    if not rows:
        return {"ok": False, "error": "Keine Result-Zeilen gefunden"}

    # Ziele bestimmen
    all_ids = [str(r.get("item_id")) for r in rows if r.get("item_id")]
    failed_ids = [str(r.get("item_id")) for r in rows if not r.get("success")] 
    target_ids = ids or (failed_ids if only_failed else all_ids)
    target_ids = [t for t in target_ids if t]

    # Patterns aus Meta rekonstruieren
    patterns = cast(List[str], meta.get("patterns") or [])
    dataset_dir = getattr(run_eval, "DEFAULT_DATASET_DIR", os.path.join("eval", "datasets"))
    if not patterns:
        patt = os.path.join(
            dataset_dir,
            getattr(run_eval, "DEFAULT_FILE_PATTERN", "eval-*.jsonl"),
        )
        patterns = [patt]
    # Relative Dateinamen ohne Ordner gegen DEFAULT_DATASET_DIR auflösen
    norm_patterns: List[str] = []
    for p in patterns:
        p_str = str(p)
        if not os.path.isabs(p_str) and (os.path.dirname(p_str) == "" or os.path.dirname(p_str) == "."):
            norm_patterns.append(os.path.join(dataset_dir, p_str))
        else:
            norm_patterns.append(p_str)
    patterns = norm_patterns

    # Items laden
    items = await run_eval.load_evaluation_items(patterns)
    id2item = {str(it.id): it for it in items}
    todo = [id2item[i] for i in target_ids if i in id2item]
    if not todo:
        return {"ok": False, "error": "Keine passenden Items zu den Ziel-IDs gefunden"}

    # Laufparameter aus Meta und Overrides
    enabled_checks = cast(Optional[List[str]], meta.get("enabled_checks"))
    eval_mode = bool(meta.get("eval_mode", True))
    asgi = bool(meta.get("asgi", True))
    api_url = cast(str, meta.get("api_url") or getattr(run_eval, "DEFAULT_API_URL", "http://localhost:8000/chat"))
    overrides = cast(Dict[str, Any], meta.get("overrides") or {})
    model_override = overrides.get("model") or meta.get("model")
    temperature_override = overrides.get("temperature") if overrides.get("temperature") is not None else meta.get("temperature")
    host_override = overrides.get("host") or meta.get("host")
    top_p_override = overrides.get("top_p")
    num_predict_override = overrides.get("num_predict")
    retries = int(meta.get("retries") or 0)

    # Output-Datei vorbereiten
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    out_dir = getattr(run_eval, "DEFAULT_RESULTS_DIR", os.path.join("eval", "results"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"results_{ts}_rerun.jsonl")

    # Optional ASGI-Client
    asgi_client: Optional[httpx.AsyncClient] = None
    if asgi:
        from app.main import app as fastapi_app
        transport = httpx.ASGITransport(app=fastapi_app)
        asgi_client = httpx.AsyncClient(transport=transport, base_url="http://asgi")
        api_url = "/chat"

    # Meta-Header schreiben
    meta2 = dict(meta)
    meta2["overrides"] = {
        "model": model_override,
        "temperature": temperature_override,
        "host": host_override,
        "top_p": top_p_override,
        "num_predict": num_predict_override,
    }
    meta2["rerun_from"] = os.path.basename(results_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": True, **meta2}, ensure_ascii=False) + "\n")

    # Items ausführen
    written = 0
    for it in todo:
        rid = f"rerun-{ts}-{it.id}"
        res = await run_eval.evaluate_item(
            it,
            api_url=api_url,
            eval_mode=eval_mode,
            client=asgi_client,
            enabled_checks=enabled_checks,
            model_override=model_override,
            temperature_override=temperature_override,
            host_override=host_override,
            top_p_override=top_p_override,
            num_predict_override=num_predict_override,
            request_id=rid,
            retries=retries,
            cache=None,
        )
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(cast(Dict[str, Any], res.__dict__), ensure_ascii=False) + "\n")
        written += 1

    if asgi_client:
        await asgi_client.aclose()

    return {"ok": True, "out": out_path, "count": written, "ids": target_ids}


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Rerun (profile-aware) aus results_*.jsonl")
    ap.add_argument("results", help="Pfad zur results_*.jsonl")
    ap.add_argument("--all", action="store_true", help="Nicht nur Fehlfälle, sondern alle Items erneut ausführen")
    ap.add_argument("--ids", type=str, default="", help="Kommagetrennte Item-IDs (überschreibt --all/Fehlfälle)")
    args = ap.parse_args(argv)

    ids = [s.strip() for s in args.ids.split(",") if s.strip()] or None
    out = asyncio.run(rerun_from_results(args.results, only_failed=(not args.all and not ids), ids=ids))
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
