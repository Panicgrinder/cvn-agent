#!/usr/bin/env python
"""
Liest Coverage-Daten (.coverage/coverage.xml) und schreibt einen Snapshot-Bericht unter
  eval/results/reports/coverage/<YYYYMMDD_HHMM>/{report.md, params.txt}.
Falls keine coverage.xml existiert, wird ein kurzer Hinweis geschrieben.
"""
from __future__ import annotations

import os
import json
import sys
from typing import Any, Dict, List, TypedDict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.time_utils import now_compact  # noqa: E402

REPORTS_ROOT = os.path.join(ROOT, "eval", "results", "reports", "coverage")

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def timestamp() -> str:
    return now_compact()


class PkgSummary(TypedDict, total=False):
    name: str | None
    branch_rate: str | None
    line_rate: str | None


def parse_coverage_xml(fp: str) -> Dict[str, Any]:
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(fp)
        root = tree.getroot()
        # Cobertura-Format: root tag ist "coverage"; Attribute line-rate, branch-rate etc.
        data: Dict[str, Any] = {
            "line_rate": root.attrib.get("line-rate"),
            "branch_rate": root.attrib.get("branch-rate"),
            "timestamp_attr": root.attrib.get("timestamp"),
        }
        # Summaries pro package/file optional sammeln
        packages: List[PkgSummary] = []
        for pkg in root.findall("packages/package"):
            pname = pkg.attrib.get("name")
            pr = pkg.attrib.get("branch-rate")
            lr = pkg.attrib.get("line-rate")
            packages.append({"name": pname, "branch_rate": pr, "line_rate": lr})
        data["packages"] = packages
        return data
    except Exception as e:
        return {"error": str(e)}


def write_files(out_dir: str, params: Dict[str, Any], content: Dict[str, Any]) -> None:
    with open(os.path.join(out_dir, "params.txt"), "w", encoding="utf-8") as f:
        f.write(json.dumps(params, ensure_ascii=False, indent=2))
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write("# Coverage Report\n\n")
        f.write(f"Zeitpunkt: {params['timestamp']}\n\n")
        cov_xml = params.get("coverage_xml")
        if not cov_xml or not os.path.exists(cov_xml):
            f.write("Es liegt keine coverage.xml vor. Bitte mit pytest --cov --cov-report=xml erzeugen.\n")
            return
        if "error" in content:
            f.write(f"Fehler beim Parsen: {content['error']}\n")
            return
        line_rate = content.get("line_rate")
        branch_rate = content.get("branch_rate")
        f.write("## Gesamt\n\n")
        f.write(f"- line-rate: {line_rate}\n")
        f.write(f"- branch-rate: {branch_rate}\n\n")
        if content.get("packages"):
            f.write("## Pakete\n\n")
            for pkg in content["packages"]:
                f.write(f"- {pkg['name']}: line-rate={pkg['line_rate']} branch-rate={pkg['branch_rate']}\n")


def main() -> int:
    ts = timestamp()
    out_dir = os.path.join(REPORTS_ROOT, ts)
    ensure_dir(out_dir)

    cov_xml = os.path.join(ROOT, "coverage.xml")
    if not os.path.exists(cov_xml):
        params = {"timestamp": ts, "coverage_xml": cov_xml}
        write_files(out_dir, params, {})
        print(f"Coverage-Report (placeholder) erzeugt: {out_dir}")
        return 0

    content = parse_coverage_xml(cov_xml)
    params = {"timestamp": ts, "coverage_xml": cov_xml}
    write_files(out_dir, params, content)
    print(f"Coverage-Report erzeugt: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
