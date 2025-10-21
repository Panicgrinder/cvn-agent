#!/usr/bin/env python
"""
Summarize evaluation results (results_*.jsonl) into a compact Markdown report.

Usage:
  python scripts/summarize_eval_results.py --tag TAG [--out docs/reports/TAG.md]
  python scripts/summarize_eval_results.py --file eval/results/results_*.jsonl [--out ...]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _find_results_by_tag(tag: str, base_dir: str) -> Optional[str]:
    pattern = os.path.join(base_dir, f"results_*_{tag}.jsonl")
    candidates = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return candidates[0] if candidates else None


def _load_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                # skip malformed lines
                continue
    return rows


def _summarize(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(rows)
    success = sum(1 for r in rows if r.get("success") is True)
    durations = [int(r.get("duration_ms", 0)) for r in rows if isinstance(r.get("duration_ms"), (int, float))]
    avg_ms = int(sum(durations) / len(durations)) if durations else 0

    # failed checks frequency
    fail_counts: Dict[str, int] = {}
    for r in rows:
        if not r.get("success"):
            for ck in (r.get("failed_checks") or []):
                if isinstance(ck, str):
                    fail_counts[ck] = fail_counts.get(ck, 0) + 1

    # package breakdown
    pkg_stats: Dict[str, Tuple[int, int, List[int]]] = {}
    for r in rows:
        pkg = str(r.get("source_package") or "")
        ok = 1 if r.get("success") else 0
        lst = pkg_stats.get(pkg, (0, 0, []))
        pkg_stats[pkg] = (lst[0] + ok, (lst[1] + 1), lst[2] + [int(r.get("duration_ms", 0))])

    pkg_lines: List[str] = []
    for pkg, (ok, cnt, times) in pkg_stats.items():
        if not pkg:
            continue
        avg = int(sum(times) / len(times)) if times else 0
        pkg_lines.append(f"- {pkg}: {ok}/{cnt} (∅ {avg} ms)")
    pkg_lines.sort()

    # top failures (sorted by count desc)
    top_fail = sorted(fail_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "total": total,
        "success": success,
        "avg_ms": avg_ms,
        "pkg_lines": pkg_lines,
        "top_fail": top_fail,
    }


def _write_markdown(out_path: str, tag: str, results_path: str, summary: Dict[str, Any]) -> None:
    total = summary["total"]
    success = summary["success"]
    avg_ms = summary["avg_ms"]
    pkg_lines = summary["pkg_lines"]
    top_fail = summary["top_fail"]

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Overnight Evaluation\n\n")
        f.write(f"- Tag: {tag}\n")
        f.write("- Modus: ASGI (in-process)\n")
        f.write(f"- Ergebnisse: {results_path}\n\n")
        f.write("## Zusammenfassung\n\n")
        f.write(f"- Erfolgreich: {success}/{total} ({(success/total*100) if total else 0:.1f}%)\n")
        f.write(f"- Durchschnittliche Dauer: {avg_ms} ms\n\n")
        if top_fail:
            f.write("Top-Fehlschlagursachen\n\n")
            for name, cnt in top_fail[:5]:
                f.write(f"- {name}: {cnt}\n")
            f.write("\n")
        if pkg_lines:
            f.write("Pakete\n\n")
            for line in pkg_lines:
                f.write(line + "\n")
            f.write("\n")
        f.write("Hinweise\n\n")
        f.write("- Vollständiger Run: Task 'Eval: overnight (auto report)' ohne Limit nutzen.\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", help="Run tag used in results filename (suffix after last underscore)")
    parser.add_argument("--file", help="Path to results_*.jsonl to summarize")
    parser.add_argument("--out", help="Output markdown path", default="")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    results_dir = project_root / "eval" / "results"

    if args.file:
        res_path = args.file
    elif args.tag:
        found = _find_results_by_tag(args.tag, str(results_dir))
        if not found:
            raise SystemExit(f"Keine results_*_{args.tag}.jsonl unter {results_dir} gefunden")
        res_path = found
    else:
        # latest fallback
        cand = sorted(glob.glob(str(results_dir / "results_*.jsonl")), key=os.path.getmtime, reverse=True)
        if not cand:
            raise SystemExit("Keine results_*.jsonl gefunden")
        res_path = cand[0]
        args.tag = Path(res_path).stem.split("_")[-1]

    rows = _load_jsonl(res_path)
    summary = _summarize(rows)

    out_path = args.out or str(project_root / "docs" / "reports" / f"{args.tag}.md")
    _write_markdown(out_path, args.tag, res_path, summary)
    print(out_path)


if __name__ == "__main__":
    main()
