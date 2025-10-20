from __future__ import annotations

import os
from pathlib import Path
import io
from contextlib import redirect_stdout
import importlib
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_open_latest_summary_opens_latest(monkeypatch: "pytest.MonkeyPatch", tmp_path: "os.PathLike[str]") -> None:
    sums_dir = Path(tmp_path) / "eval" / "results" / "summaries"
    os.makedirs(sums_dir, exist_ok=True)
    # Note: module uses SUMMARY_GLOB = "summary_ALL_*_MIXED.md"
    older = sums_dir / "summary_ALL_20240101_MIXED.md"
    newer = sums_dir / "summary_ALL_20251231_MIXED.md"
    older.write_text("old", encoding="utf-8")
    newer.write_text("new", encoding="utf-8")

    mod = importlib.import_module("scripts.open_latest_summary")

    opened: dict[str, str] = {}

    def fake_open_file(p: Path) -> None:
        opened["path"] = str(p)

    monkeypatch.setattr(mod, "open_file", fake_open_file)

    import sys
    old_argv = sys.argv[:]
    sys.argv = ["open_latest_summary.py", "--dir", str(sums_dir)]
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = mod.main()
        out = buf.getvalue()
        assert rc == 0
        assert "Opening" in out
    finally:
        sys.argv = old_argv

    assert opened.get("path", "").endswith("summary_ALL_20251231_MIXED.md")
