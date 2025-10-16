#!/usr/bin/env python
"""
Rerun-Failed für Eval:
- Nimmt die neueste eval/results/results_*.jsonl
- Extrahiert fehlgeschlagene IDs
- Baut ein gefiltertes JSONL-Dataset unter eval/results/tmp/ zum direkten Re-Run

Aufruf:
  python scripts/rerun_failed.py
  python scripts/run_eval.py --patterns "eval/results/tmp/rerun_*.jsonl"
"""
from __future__ import annotations
import os, glob, json, datetime as dt
from typing import List, Dict, Any, Optional, cast
from utils.eval_utils import strip_eval_prefix, ensure_eval_prefix

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(PROJECT_ROOT, "eval", "datasets")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "eval", "results")
TMP_DIR = os.path.join(RESULTS_DIR, "tmp")

def _latest_results() -> Optional[str]:
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "results_*.jsonl")))
    return files[-1] if files else None

def _load_failed_ids(path: str) -> List[str]:
    failed: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            # robust: akzeptiere verschiedene Felder
            rid = str(rec.get("id") or rec.get("item_id") or rec.get("eval_id") or "")
            success = bool(rec.get("success")) if "success" in rec else None
            error = rec.get("error")
            failed_checks: List[Any] = rec.get("failed_checks") or []  # type: ignore[assignment]
            if not rid:
                continue
            if success is False or error or (isinstance(failed_checks, list) and len(failed_checks) > 0):
                # Füge beide Schlüsselvarianten hinzu, um robust gegen Präfixe zu sein
                if rid:
                    failed.append(rid)
                    failed.append(strip_eval_prefix(rid))
                    failed.append(ensure_eval_prefix(rid))
    return sorted(set(failed))

def _load_registry() -> Dict[str, Dict[str, Any]]:
    reg: Dict[str, Dict[str, Any]] = {}
    # JSONL zuerst
    for p in glob.glob(os.path.join(DATASETS_DIR, "eval-*.jsonl")):
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                if not isinstance(obj, dict):
                    continue
                objd2: Dict[str, Any] = cast(Dict[str, Any], obj)
                rid = objd2.get("id")
                if isinstance(rid, str):
                    # Mappe sowohl mit als auch ohne eval- Präfix
                    reg[rid] = objd2
                    reg[strip_eval_prefix(rid)] = objd2
                    reg[ensure_eval_prefix(rid)] = objd2
    # JSON (Array)
    for p in glob.glob(os.path.join(DATASETS_DIR, "eval-*.json")):
        if p.endswith(".jsonl"):
            continue
        try:
            arr = json.load(open(p, "r", encoding="utf-8"))
            if isinstance(arr, list):
                arr_list: List[Any] = cast(List[Any], arr)
                for obj in arr_list:
                    if not isinstance(obj, dict):
                        continue
                    objd: Dict[str, Any] = cast(Dict[str, Any], obj)
                    rid = objd.get("id")
                    if isinstance(rid, str):
                        reg[rid] = objd
                        reg[strip_eval_prefix(rid)] = objd
                        reg[ensure_eval_prefix(rid)] = objd
        except Exception:
            continue
    return reg

def main() -> int:
    latest = _latest_results()
    if not latest:
        print("Keine results_*.jsonl gefunden unter eval/results/")
        return 1
    failed = _load_failed_ids(latest)
    if not failed:
        print(f"Keine fehlgeschlagenen IDs in {latest} gefunden.")
        return 0
    reg = _load_registry()
    items = [reg[i] for i in failed if i in reg]
    if not items:
        print("Fehlgeschlagene IDs nicht in eval/datasets gefunden.")
        return 2
    os.makedirs(TMP_DIR, exist_ok=True)
    ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(TMP_DIR, f"rerun_{ts}_{len(items)}.jsonl")
    with open(out_path, "w", encoding="utf-8") as out:
        for obj in items:
            out.write(json.dumps(obj, ensure_ascii=False) + "\n")
    # Robust gegenüber unterschiedlichen Laufwerken (Windows):
    try:
        rel = os.path.relpath(out_path, PROJECT_ROOT)
    except Exception:
        rel = out_path
    print(f"Re-Run Dataset erstellt: {rel}")
    print("Nächster Schritt:")
    print('  python scripts/run_eval.py --patterns "eval/results/tmp/rerun_*.jsonl"')
    return 0

if __name__ == "__main__":
    raise SystemExit(main())