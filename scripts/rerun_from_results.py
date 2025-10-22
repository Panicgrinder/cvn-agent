#!/usr/bin/env python
from __future__ import annotations

import os
import json
from typing import Any, Dict, List, Optional, cast
import asyncio
from utils.time_utils import now_compact


def _load_results_with_meta(path: str) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
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
    from scripts import run_eval  # [`scripts/run_eval.py`](scripts/run_eval.py)
    import httpx

    meta, rows = _load_results_with_meta(results_path)
    if not rows:
        return {"ok": False, "error": "Keine Result-Zeilen gefunden"}

    all_ids = [str(r.get("item_id")) for r in rows if r.get("item_id")]
    failed_ids = [str(r.get("item_id")) for r in rows if not r.get("success")]
    target_ids = ids or (failed_ids if only_failed else all_ids)
    target_ids = [t for t in target_ids if t]

    patterns = cast(List[str], meta.get("patterns") or [])
    base_datasets_dir = getattr(run_eval, "DEFAULT_DATASET_DIR", os.path.join("eval", "datasets"))
    if not patterns:
        patt = os.path.join(base_datasets_dir, getattr(run_eval, "DEFAULT_FILE_PATTERN", "eval-*.json"))
        patterns = [patt]
    else:
        # Lasse Basename-Patterns relativ zu DEFAULT_DATASET_DIR auflösen
        resolved: List[str] = []
        for p in patterns:
            try:
                is_abs = os.path.isabs(p)
                has_dir = bool(os.path.dirname(p))
            except Exception:
                is_abs = False
                has_dir = False
            if not is_abs and not has_dir:
                resolved.append(os.path.join(base_datasets_dir, p))
            else:
                resolved.append(p)
        patterns = resolved

    items = await run_eval.load_evaluation_items(patterns)
    id2item = {str(it.id): it for it in items}
    todo = [id2item[i] for i in target_ids if i in id2item]
    if not todo:
        return {"ok": False, "error": "Keine passenden Items zu den Ziel-IDs gefunden"}

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

    ts = now_compact()
    out_dir = getattr(run_eval, "DEFAULT_RESULTS_DIR", os.path.join("eval", "results"))
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"results_{ts}_rerun.jsonl")

    asgi_client: Optional[httpx.AsyncClient] = None
    if asgi:
        from app.main import app as fastapi_app
        transport = httpx.ASGITransport(app=fastapi_app)
        asgi_client = httpx.AsyncClient(transport=transport, base_url="http://asgi")
        api_url = "/chat"

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

    written = 0
    for it in todo:
        rid = f"rerun-{ts}-{it.id}"
        r = await run_eval.evaluate_item(
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
            f.write(json.dumps(cast(Dict[str, Any], r.__dict__), ensure_ascii=False) + "\n")
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
