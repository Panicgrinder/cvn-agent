#!/usr/bin/env python
"""
Appendet einen Eintrag zu docs/DONELOG.txt.

Nutzung:
  python scripts/append_done.py "Kurzbeschreibung der Änderung"

Optional: Autor wird aus git config user.name gelesen; sonst Nutzername der Umgebung.
"""
from __future__ import annotations

import os
import sys
import datetime as dt
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(PROJECT_ROOT, "docs", "DONELOG.txt")


def get_author() -> str:
    try:
        name = subprocess.check_output(["git", "config", "user.name"], cwd=PROJECT_ROOT, text=True).strip()
        if name:
            return name
    except Exception:
        pass
    return os.getenv("USERNAME") or os.getenv("USER") or "unknown"


def main(argv: list[str]) -> int:
    if not argv:
        print("Bitte Kurzbeschreibung angeben.")
        return 2
    msg = argv[0].strip()
    if not msg:
        print("Leere Kurzbeschreibung nicht erlaubt.")
        return 2
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    author = get_author()
    line = f"{ts} | {author} | {msg}\n"
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"DONELOG aktualisiert: {line.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
