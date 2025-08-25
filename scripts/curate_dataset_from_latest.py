#!/usr/bin/env python
"""
Kuratiert Trainingsdaten aus dem neuesten Eval-Run (results_*.jsonl):
- Wählt die neueste results_*.jsonl unter eval/results
- Exportiert in openai_chat-Format (nur erfolgreiche Antworten per Default)
- Erzeugt Train/Val-Pack (dedupliziert, minimaler Output, deterministischer Split)

Nutzung:
    python scripts/curate_dataset_from_latest.py \
    --results-dir eval/results \
    --format openai_chat \
    --train-ratio 0.9 \
    --min-output-chars 20 \
        [--include-failures] [--min-rpg-style 0.0] [--exclude-regex "pattern"] [--results-file path]

Ausgabe:
  - Exportierte JSONL unter eval/results/finetune
  - Train/Val unter eval/results/finetune
  - Kurzer JSON-Report auf stdout
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, List, cast

# Modulpfade vorbereiten
import sys
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts import export_finetune as _export
from scripts import prepare_finetune_pack as _prepare
from scripts import run_eval as _run_eval


def _latest_results(path: str) -> Optional[str]:
    files = sorted(glob.glob(os.path.join(path, "results_*.jsonl")), reverse=True)
    return files[0] if files else None


def main() -> int:
    # Dynamischer Default-Pfad über Settings
    try:
        from app.core.settings import settings
        default_results = os.path.join(os.path.dirname(os.path.dirname(__file__)), getattr(settings, "EVAL_RESULTS_DIR", "eval/results"))
    except Exception:
        default_results = os.path.join("eval", "results")
    
    p = argparse.ArgumentParser(description="Kuratiert Trainingspakete aus dem neuesten results_*.jsonl")
    p.add_argument("--results-dir", default=default_results, help=f"Verzeichnis mit results_*.jsonl (Default: {default_results})")
    p.add_argument("--format", choices=["openai_chat", "alpaca"], default="openai_chat", help="Export-Format")
    p.add_argument("--train-ratio", type=float, default=0.9, help="Train-Anteil (0-1)")
    p.add_argument("--min-output-chars", type=int, default=20, help="Mindestlänge der Ausgabe-Zeichen für Filter")
    p.add_argument("--include-failures", action="store_true", help="Auch fehlgeschlagene Antworten exportieren")
    p.add_argument("--min-rpg-style", type=float, default=0.0, help="Mindestschwelle für rpg_style Score (0..1)")
    p.add_argument("--exclude-regex", default=None, help="Regex zum Ausschließen von Items nach Instruction/Input")
    p.add_argument("--results-file", default=None, help="Konkrete results_*.jsonl statt neuester wählen")
    args = p.parse_args()

    results_dir = args.results_dir
    chosen = args.results_file or _latest_results(results_dir)
    if not chosen:
        print(json.dumps({"ok": False, "error": f"Keine results_*.jsonl in {results_dir}"}))
        return 2

    finetune_dir = os.path.join(results_dir, "finetune")
    os.makedirs(finetune_dir, exist_ok=True)

    # 1) Export
    import asyncio
    exp = asyncio.run(_export.export_from_results(
        chosen,
        out_dir=finetune_dir,
        format=args.format,
        include_failures=args.include_failures,
    ))
    if not exp.get("ok"):
        print(json.dumps({"ok": False, "error": exp.get("error")}))
        return 3

    exported_path = str(exp.get("out"))

    # Optional: Qualitätsfilter anwenden (rpg_style, exclude_regex) für openai_chat
    if args.min_rpg_style > 0.0 or args.exclude_regex:
        # Laden und filtern
        import re
        def _iter_jsonl(path: str):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    yield json.loads(line)

        records: List[Dict[str, Any]] = list(_iter_jsonl(exported_path))
        filtered: List[Dict[str, Any]] = []
        pattern = re.compile(args.exclude_regex) if args.exclude_regex else None
        for rec in records:
            if args.format == "openai_chat":
                msgs = cast(List[Dict[str, str]], rec.get("messages") or [])
                # rpg_style Score über gesamten Assistant-Output beurteilen
                text = "\n".join([str(m.get("content", "")) for m in msgs if str(m.get("role")) == "assistant"])  # type: ignore[index]
            else:
                text = str(rec.get("output", ""))
            score = float(_run_eval.rpg_style_score(text))
            if score < args.min_rpg_style:
                continue
            if pattern is not None:
                # Instruction/Input heranziehen
                if args.format == "openai_chat":
                    msgs2 = cast(List[Dict[str, str]], rec.get("messages") or [])
                    instruction = next((str(m.get("content", "")) for m in msgs2 if str(m.get("role")) == "user"), "")
                    other = "\n".join([str(m.get("content", "")) for m in msgs2 if str(m.get("role")) != "user"]) or ""
                    hay = f"{instruction}\n{other}"
                else:
                    instruction = str(rec.get("instruction", ""))
                    inp = str(rec.get("input", ""))
                    hay = f"{instruction}\n{inp}"
                if pattern.search(hay):
                    continue
            filtered.append(rec)

        # Falls alles herausgefiltert wurde, abbrechen mit Info
        if not filtered:
            print(json.dumps({
                "ok": False,
                "error": "Alle Einträge wurden durch Filter ausgeschlossen",
                "results": chosen,
                "export": exported_path,
                "filters": {
                    "min_rpg_style": args.min_rpg_style,
                    "exclude_regex": args.exclude_regex,
                }
            }, ensure_ascii=False))
            return 5

        # Überschreiben exportierter Datei mit gefilterten Einträgen
        with open(exported_path, "w", encoding="utf-8") as f:
            for r in filtered:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # 2) Train/Val Pack
    pack = _prepare.prepare_pack(
        src_path=exported_path,
        out_dir=finetune_dir,
        format=args.format,
        train_ratio=args.train_ratio,
        seed=42,
        min_output_chars=args.min_output_chars,
        dedupe_by_instruction=True,
    )
    if not pack.get("ok"):
        print(json.dumps({"ok": False, "error": pack.get("error")}))
        return 4

    report: Dict[str, Any] = {
        "ok": True,
        "timestamp": datetime.now().strftime("%Y%m%d_%H%M"),
    "results": chosen,
        "export": exported_path,
        "train": pack.get("train"),
        "val": pack.get("val"),
        "counts": pack.get("counts"),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
