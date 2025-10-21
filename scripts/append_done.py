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
    # Nutze zentrale Zeit-Helfer; Fallback auf lokale Systemzeit
    try:
        from utils.time_utils import now_human_tz, tz_label  # type: ignore
        ts = now_human_tz()
        tz_info = tz_label()
    except Exception:
        ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        tz_info = ""
    author = get_author()
    line = f"{ts} | {author} | {msg}\n"
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    # Optional: Header um Zeitzonenhinweis ergänzen, falls CVN_TZ gesetzt ist
    try:
        tz_env = os.getenv("CVN_TZ") or os.getenv("TZ")
        if tz_env and os.path.exists(LOG_PATH):
            with open(LOG_PATH, "r", encoding="utf-8") as f:
                content = f.read()
            if "Zeitzone:" not in content.splitlines()[0]:
                # Füge eine Hinweiszeile nach der ersten Überschrift hinzu
                lines = content.splitlines()
                insert_idx = 1 if lines and lines[0].startswith("# DONELOG") else 0
                lines.insert(insert_idx, f"Zeitzone: {tz_env} ({tz_info})")
                with open(LOG_PATH, "w", encoding="utf-8") as f:
                    f.write("\n".join(lines) + "\n")
    except Exception:
        pass
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line)
    print(f"DONELOG aktualisiert: {line.strip()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
