from __future__ import annotations

import importlib
from pathlib import Path
import io
import contextlib
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_open_latest_summary_error_when_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.open_latest_summary")
    d = tmp_path / "eval" / "results" / "summaries"
    d.mkdir(parents=True)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        # simulate CLI
        import sys
        sys.argv = ["open_latest_summary.py", "--dir", str(d)]
        rc = mod.main()
    assert rc == 2
    assert "No summaries found" in buf.getvalue()


@pytest.mark.scripts
@pytest.mark.unit
def test_open_latest_summary_happy_print(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.open_latest_summary")
    d = tmp_path / "eval" / "results" / "summaries"
    d.mkdir(parents=True)
    # create multiple matching files; latest lexicographically last
    (d / "summary_ALL_20250101_0101_MIXED.md").write_text("A", encoding="utf-8")
    (d / "summary_ALL_20250102_0101_MIXED.md").write_text("B", encoding="utf-8")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import sys
        sys.argv = ["open_latest_summary.py", "--dir", str(d), "--print"]
        rc = mod.main()
    assert rc == 0
    out = buf.getvalue().strip()
    assert out.endswith("summary_ALL_20250102_0101_MIXED.md")