#!/usr/bin/env python
"""
Sammelt Status-/Metrik-Daten für docs/TODO.md:
- Neueste Eval-Ergebnisse analysieren (Erfolgsrate, RPG-Anteil, Dauer)
- Verfügbarkeit offener Features prüfen (Caching, Rerun-Failed, Fine-Tune-Skript)
- Optional Markdown-Report schreiben

Aufruf:
  python scripts/todo_gather.py --write-md
"""
from __future__ import annotations
import os, glob, json, argparse
from typing import Any, Dict, List, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "eval", "results")
SUMMARIES_DIR = os.path.join(RESULTS_DIR, "summaries")

def latest_results() -> Optional[str]:
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "results_*.jsonl")))
    return files[-1] if files else None

def parse_results(path: str) -> Dict[str, Any]:
    total = 0
    success = 0
    rpg_mode = 0
    durations: List[int] = []
    failed_ids: List[str] = []
    by_package: Dict[str, Dict[str, Any]] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            total += 1
            if r.get("success") is True:
                success += 1
            if r.get("rpg_mode") is True:
                rpg_mode += 1
            d = r.get("duration_ms")
            if isinstance(d, (int, float)):
                durations.append(int(d))
            rid = r.get("id") or r.get("item_id")
            if r.get("success") is not True and rid:
                failed_ids.append(str(rid))
            pkg = r.get("package") or "unknown"
            stats = by_package.setdefault(str(pkg), {"total": 0, "success": 0, "durations": []})
            stats["total"] += 1
            if r.get("success") is True:
                stats["success"] += 1
            if isinstance(d, (int, float)):
                stats["durations"].append(int(d))
    avg_dur = (sum(durations)/len(durations)) if durations else 0.0
    return {
        "path": path,
        "total": total,
        "success": success,
        "success_rate": (success/total*100.0) if total else 0.0,
        "rpg_percentage": (rpg_mode/total*100.0) if total else 0.0,
        "avg_duration_ms": avg_dur,
        "failed_ids": sorted(set(failed_ids)),
        "by_package": by_package,
    }

def file_exists(rel: str) -> bool:
    return os.path.exists(os.path.join(PROJECT_ROOT, rel))

def feature_status() -> Dict[str, Any]:
    # Caching: Datei + Nutzung in map_reduce_summary_llm.py
    caching_file = file_exists("utils/eval_cache.py")
    caching_used = False
    if file_exists("scripts/map_reduce_summary_llm.py"):
        try:
            txt = open(os.path.join(PROJECT_ROOT, "scripts", "map_reduce_summary_llm.py"), "r", encoding="utf-8").read()
            caching_used = ("utils.eval_cache" in txt) or ("cache_llm.jsonl" in txt)
        except Exception:
            pass
    rerun_failed = False  # legacy script replaced by rerun_from_results.py
    fine_tune = file_exists("scripts/fine_tune_pipeline.py")
    curate = file_exists("scripts/curate_dataset_from_latest.py")
    return {
        "caching_available": caching_file,
        "caching_integrated": caching_used,
        "rerun_failed_available": rerun_failed,
        "fine_tune_pipeline_available": fine_tune,
        "curate_dataset_available": curate,
    }

def build_md(results: Optional[Dict[str, Any]], features: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# TODO-Status – Automatischer Überblick")
    lines.append("")
    lines.append("## Features (offene Punkte)")
    lines.append(f"- Caching/Memoization: {'✅ integriert' if features['caching_integrated'] else ('🟡 vorhanden (noch nicht integriert)' if features['caching_available'] else '❌ fehlt')}")
    lines.append(f"- Rerun-Failed: ✅ via scripts/rerun_from_results.py")
    lines.append(f"- Fine-Tuning/LoRA Pipeline: {'✅ vorhanden' if features['fine_tune_pipeline_available'] else '❌ fehlt'}")
    lines.append(f"- Datensatzkurierung: {'✅ vorhanden' if features['curate_dataset_available'] else '❌ fehlt'}")
    lines.append("")
    if results:
        lines.append("## Letzte Eval-Metriken")
        lines.append(f"- Datei: {os.path.relpath(results['path'], PROJECT_ROOT)}")
        lines.append(f"- Tests: {results['success']}/{results['total']} ({results['success_rate']:.1f}%)")
        lines.append(f"- RPG-Anteil: {results['rpg_percentage']:.1f}%")
        lines.append(f"- Ø Dauer: {results['avg_duration_ms']:.0f} ms")
        if results["failed_ids"]:
            lines.append(f"- Fehlgeschlagene IDs: {', '.join(results['failed_ids'][:25])}{' …' if len(results['failed_ids'])>25 else ''}")
    return "\n".join(lines)

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-md", action="store_true", help="Schreibt Markdown-Report unter eval/results/summaries/")
    args = ap.parse_args(argv)
    latest = latest_results()
    results = parse_results(latest) if latest else None
    features = feature_status()
    md = build_md(results, features)
    print(md)
    if args.write_md:
        os.makedirs(SUMMARIES_DIR, exist_ok=True)
        from utils.time_utils import now_compact
        ts = now_compact()
        out = os.path.join(SUMMARIES_DIR, f"todo_status_{ts}.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(md + "\n")
        print(f"\nReport gespeichert: {os.path.relpath(out, PROJECT_ROOT)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())