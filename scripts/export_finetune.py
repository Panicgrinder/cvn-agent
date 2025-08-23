#!/usr/bin/env python
"""
Exportiert Finetuning-Datensätze (SFT/OpenAI-Chat) aus einer results_*.jsonl-Datei.

Formate:
- alpaca: { instruction, input, output, meta }
- openai_chat: { messages: [{role, content}, ...], meta }

Standard: Nur erfolgreiche Antworten exportieren.
"""
from __future__ import annotations

import os
import sys
import json
from typing import Any, Dict, List, Optional, Tuple, cast
from datetime import datetime


def _load_run_eval_module():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    import importlib.util
    run_eval_path = os.path.join(project_root, "scripts", "run_eval.py")
    spec = importlib.util.spec_from_file_location("run_eval", run_eval_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Konnte run_eval.py nicht laden")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


run_eval = _load_run_eval_module()


def _load_results(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict):
                continue
            data: Dict[str, Any] = cast(Dict[str, Any], raw)
            if data.get("_meta") is True:
                continue
            rows.append(data)
    return rows


async def _load_items_map(patterns: Optional[List[str]] = None) -> Dict[str, Any]:
    items = await run_eval.load_evaluation_items(patterns)
    return {it.id: it for it in items}


def _first_user_message(messages: List[Dict[str, str]]) -> Tuple[str, str]:
    """Liefert (instruction, input)."""
    if not messages:
        return ("", "")
    # Nimm erste user-Nachricht als Instruction, Rest als Input-Zusammenfassung
    instruction = next((m["content"] for m in messages if m.get("role") == "user"), messages[0].get("content", ""))
    others = [m["content"] for m in messages if m.get("role") != "user"]
    input_text = "\n\n".join(others) if others else ""
    return (instruction or "", input_text)


async def export_from_results(
    results_path: str,
    out_dir: Optional[str] = None,
    format: str = "alpaca",
    include_failures: bool = False,
    patterns: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if out_dir is None:
        out_dir_str: str = str(getattr(run_eval, "DEFAULT_RESULTS_DIR", run_eval.DEFAULT_EVAL_DIR))
    else:
        out_dir_str = str(out_dir)
    os.makedirs(out_dir_str, exist_ok=True)

    rows = _load_results(results_path)
    if not rows:
        return {"ok": False, "error": "Keine Ergebnisse in Datei"}

    # Map Items laden
    id2item = await _load_items_map(patterns or [os.path.join(run_eval.DEFAULT_EVAL_DIR, run_eval.DEFAULT_FILE_PATTERN)])

    # Filter
    if not include_failures:
        rows = [r for r in rows if r.get("success")]

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    base = os.path.splitext(os.path.basename(results_path))[0]
    out_path: str = os.path.join(out_dir_str, f"finetune_{format}_{base}_{timestamp}.jsonl")

    count = 0
    with open(out_path, "w", encoding="utf-8") as out:
        for r in rows:
            item_id = r.get("item_id")
            if not item_id:
                continue
            item = id2item.get(item_id)
            if not item:
                # Item evtl. nicht in aktuellen Paketen; überspringen
                continue
            messages = cast(List[Dict[str, str]], item.messages or [])
            response = r.get("response", "")

            if format == "alpaca":
                instr, inp = _first_user_message(messages)
                rec: Dict[str, Any] = {
                    "instruction": instr,
                    "input": inp,
                    "output": response,
                    "meta": {
                        "id": item_id,
                        "package": item.source_package,
                        "success": bool(r.get("success")),
                        "failed_checks": r.get("failed_checks", []),
                    },
                }
            elif format == "openai_chat":
                # Bewahre alle bisherigen Nachrichten, hänge Assistant-Output an
                msgs: List[Dict[str, str]] = list(messages)
                msgs.append({"role": "assistant", "content": response})
                rec: Dict[str, Any] = {
                    "messages": msgs,
                    "meta": {
                        "id": item_id,
                        "package": item.source_package,
                        "success": bool(r.get("success")),
                        "failed_checks": r.get("failed_checks", []),
                    },
                }
            else:
                raise ValueError("Unbekanntes Format: " + format)

            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            count += 1

    return {"ok": True, "out": out_path, "count": count}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Exportiert Fine-Tuning-Datensatz aus results_*.jsonl")
    parser.add_argument("results", help="Pfad zur results_*.jsonl Datei")
    parser.add_argument("--format", choices=["alpaca", "openai_chat"], default="alpaca")
    parser.add_argument("--include-failures", action="store_true", help="Auch fehlgeschlagene Antworten exportieren")
    args = parser.parse_args()

    res = __import__(__name__)
    import asyncio
    out = asyncio.run(export_from_results(args.results, format=args.format, include_failures=args.include_failures))
    if out.get("ok"):
        print(f"Export: {out['out']} ({out['count']} Einträge)")
    else:
        print("Fehler:", out.get("error"))
