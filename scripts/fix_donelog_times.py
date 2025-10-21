#!/usr/bin/env python
"""
Normalisiert Zeitstempel in docs/DONELOG.txt anhand von git blame (author-time).

Verwendung:
  python scripts/fix_donelog_times.py

Respektiert optionale Zeitzone via CVN_TZ/TZ (z.B. Europe/Berlin). Fällt sonst
auf System-Lokalzeit (aware, mit Offset) zurück.
"""
from __future__ import annotations

import os
import re
import subprocess
from datetime import datetime

try:
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DONELOG = os.path.join(PROJECT_ROOT, "docs", "DONELOG.txt")


def _tz():
    name = os.getenv("CVN_TZ") or os.getenv("TZ")
    if name and ZoneInfo is not None:
        try:
            return ZoneInfo(name)
        except Exception:
            return None
    return None


def _fmt_epoch(epoch: int) -> str:
    tz = _tz()
    dt = datetime.fromtimestamp(epoch, tz=tz) if tz is not None else datetime.fromtimestamp(epoch).astimezone()
    return dt.strftime("%Y-%m-%d %H:%M")


def blame_times(path: str) -> dict[int, int]:
    """Mappt 1-basierte Zeilennummer -> author-time (epoch)."""
    out = subprocess.check_output(["git", "blame", "--line-porcelain", path], text=True)
    times: dict[int, int] = {}
    current_time = None
    current_lineno = None
    for ln in out.splitlines():
        if ln.startswith("author-time "):
            try:
                current_time = int(ln.split()[1])
            except Exception:
                current_time = None
        elif ln.startswith("lineno "):
            try:
                current_lineno = int(ln.split()[1])
            except Exception:
                current_lineno = None
            if current_lineno is not None and current_time is not None:
                times[current_lineno] = current_time
    return times


def normalize() -> int:
    with open(DONELOG, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    times = blame_times(DONELOG)
    pat = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) \|")

    # Finde Start der Einträge
    start = 0
    for i, l in enumerate(lines):
        if pat.match(l):
            start = i
            break

    new_lines = lines[:start]
    changed = 0
    for idx in range(start, len(lines)):
        l = lines[idx]
        m = pat.match(l)
        if not m:
            new_lines.append(l)
            continue
        blame_idx = idx + 1  # 1-basiert
        epoch = times.get(blame_idx)
        if not epoch:
            new_lines.append(l)
            continue
        ts = _fmt_epoch(epoch)
        if ts != m.group(1):
            changed += 1
        new_lines.append(ts + l[m.end(1):])

    if changed:
        with open(DONELOG, "w", encoding="utf-8") as f:
            f.write("\n".join(new_lines) + "\n")
        print(f"DONELOG aktualisiert: {changed} Zeitstempel angepasst.")
    else:
        print("DONELOG unverändert: Keine Zeitstempel-Anpassung notwendig.")
    return 0


if __name__ == "__main__":
    raise SystemExit(normalize())
