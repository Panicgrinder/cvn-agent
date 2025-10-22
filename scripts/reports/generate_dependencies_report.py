#!/usr/bin/env python
"""
Generates a dependencies report and stores it under
  eval/results/reports/dependencies/<YYYYMMDD_HHMM>/{report.md, params.txt}
It runs scripts/dependency_check.py and captures its output.
"""
from __future__ import annotations

import os
import sys
import io
import json
from typing import Any, Dict, List

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

REPORTS_ROOT = os.path.join(ROOT, "eval", "results", "reports", "dependencies")

# Import erst NACH dem sys.path-Patch
from utils.time_utils import now_compact  # noqa: E402


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def timestamp() -> str:
    return now_compact()


def run_dependency_checks() -> List[str]:
    """Import dependency_check and capture its stdout output as a list of lines."""
    import importlib.util

    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        spec = importlib.util.spec_from_file_location("dependency_check", os.path.join(ROOT, "scripts", "dependency_check.py"))
        if spec is None or spec.loader is None:
            print("[ERR] Could not create ModuleSpec for dependency_check.py")
            return []
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        if hasattr(mod, "main"):
            mod.main()
        else:
            print("[ERR] dependency_check.main() is missing")
    finally:
        sys.stdout = old_stdout
    output = buf.getvalue()
    lines = [ln.rstrip() for ln in output.splitlines() if ln.strip()]
    return lines


def write_files(out_dir: str, params: Dict[str, Any], lines: List[str]) -> None:
    # params.txt: JSON metadata
    with open(os.path.join(out_dir, "params.txt"), "w", encoding="utf-8") as f:
        f.write(json.dumps(params, ensure_ascii=False, indent=2))
    # report.md: compact report
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("# Dependencies Report\n\n")
        f.write(f"Timestamp: {params['timestamp']}\n\n")
        f.write("## Summary\n\n")
        if not lines:
            f.write("No output captured.\n")
        else:
            for ln in lines:
                f.write(f"- {ln}\n")


def main() -> int:
    ts = timestamp()
    out_dir = os.path.join(REPORTS_ROOT, ts)
    ensure_dir(out_dir)

    lines = run_dependency_checks()
    params: Dict[str, Any] = {
        "timestamp": ts,
        "source": "scripts/reports/generate_dependencies_report.py",
        "tools": ["scripts/dependency_check.py"],
    }
    write_files(out_dir, params, lines)
    print(f"Dependencies report created: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
