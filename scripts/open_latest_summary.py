from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional
import webbrowser

SUMMARY_DIR = Path(__file__).resolve().parents[1] / "eval" / "results" / "summaries"
SUMMARY_GLOB = "summary_ALL_*_MIXED.md"


def find_latest_summary(dir_path: Path = SUMMARY_DIR) -> Optional[Path]:
    if not dir_path.exists():
        return None
    candidates = sorted(dir_path.glob(SUMMARY_GLOB))
    if not candidates:
        return None
    # Files are timestamped; sorted() ensures lexicographic order; latest is last
    return candidates[-1]


def open_file(path: Path) -> None:
    # Try default browser first (works for markdown viewers too)
    try:
        webbrowser.open(path.as_uri())
        return
    except Exception:
        pass
    # Fallback: OS-specific open
    if sys.platform.startswith("win"):
        os.startfile(str(path))
    elif sys.platform == "darwin":
        os.system(f"open '{path}'")
    else:
        os.system(f"xdg-open '{path}'")


def main() -> int:
    parser = argparse.ArgumentParser(description="Open the latest merged workspace summary.")
    parser.add_argument("--print", dest="do_print", action="store_true", help="Only print the path without opening it")
    parser.add_argument("--dir", dest="dir", default=str(SUMMARY_DIR), help="Directory to search (default: eval/results/summaries)")
    args = parser.parse_args()

    dir_path = Path(args.dir)
    latest = find_latest_summary(dir_path)
    if latest is None:
        print(f"No summaries found in {dir_path} matching {SUMMARY_GLOB}")
        return 2

    if args.do_print:
        print(str(latest))
        return 0

    print(f"Opening {latest}")
    open_file(latest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
