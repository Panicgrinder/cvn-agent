#!/usr/bin/env python
"""
Führt das lokale Konsistenz-Audit aus (scripts/audit_workspace.py) und schreibt
  eval/results/reports/consistency/<YYYYMMDD_HHMM>/{report.md, params.txt}
"""
from __future__ import annotations

import os
import sys
import io
import json
from typing import Any, Dict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
REPORTS_ROOT = os.path.join(ROOT, "eval", "results", "reports", "consistency")

# Import erst NACH dem sys.path-Patch, sonst schlägt der Import in direkter Ausführung fehl
from utils.time_utils import now_compact  # noqa: E402


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def timestamp() -> str:
    return now_compact()


def run_audit_workspace() -> str:
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        audit_main = None  # type: ignore[assignment]
        # Try to import as module first; fallback to spec from file
        try:
            from scripts.audit_workspace import main as audit_main  # type: ignore
        except Exception:
            import importlib.util as _util
            audit_path = os.path.join(ROOT, "scripts", "audit_workspace.py")
            spec = _util.spec_from_file_location("audit_workspace", audit_path)
            if spec is None or spec.loader is None:
                print("[ERR] Could not load scripts/audit_workspace.py")
            else:
                mod = _util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                audit_main = getattr(mod, "main", None)
        if callable(audit_main):
            audit_main()
        else:
            print("[ERR] audit_workspace.main() not callable")
    finally:
        sys.stdout = old_stdout
    return buf.getvalue()


def write_files(out_dir: str, params: Dict[str, Any], text: str) -> None:
    with open(os.path.join(out_dir, "params.txt"), "w", encoding="utf-8") as f:
        f.write(json.dumps(params, ensure_ascii=False, indent=2))
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("# Konsistenz-Report\n\n")
        f.write(f"Zeitpunkt: {params['timestamp']}\n\n")
        f.write("## audit_workspace Output\n\n")
        if text.strip():
            for ln in text.splitlines():
                f.write(f"- {ln}\n")
        else:
            f.write("(keine Ausgabe)\n")


def main() -> int:
    ts = timestamp()
    out_dir = os.path.join(REPORTS_ROOT, ts)
    ensure_dir(out_dir)

    out = run_audit_workspace()
    params: Dict[str, Any] = {
        "timestamp": ts,
        "source": "scripts/reports/generate_consistency_report.py",
        "tools": ["scripts/audit_workspace.py"],
    }
    write_files(out_dir, params, out)
    print(f"Konsistenz-Report erzeugt: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
