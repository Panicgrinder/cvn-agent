from __future__ import annotations

import os
from pathlib import Path
import io
from contextlib import redirect_stdout
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_open_latest_summary_find_and_print(monkeypatch: "pytest.MonkeyPatch", tmp_path: "os.PathLike[str]") -> None:
    # Erzeuge zwei Dummy-Summary-Dateien im tmp-Summaries-Ordner
    sums_dir = Path(tmp_path) / "eval" / "results" / "summaries"
    os.makedirs(sums_dir, exist_ok=True)
    f1 = sums_dir / "summary_ALL_20250101.md"
    f2 = sums_dir / "summary_ALL_20251231.md"
    f1.write_text("A", encoding="utf-8")
    f2.write_text("B", encoding="utf-8")

    from scripts import open_latest_summary as mod
    # Patch den Default-SUMMARY_DIR auf unseren tmp-Pfad
    monkeypatch.setattr(mod, "SUMMARY_DIR", sums_dir)
    # Weite den Glob aus, damit er die erzeugten Dateien findet
    monkeypatch.setattr(mod, "SUMMARY_GLOB", "summary_ALL_*.md")

    latest = mod.find_latest_summary(sums_dir)
    assert latest is not None and latest.name == "summary_ALL_20251231.md"

    # Teste main() im print-only Modus
    import sys
    old_argv = sys.argv[:]
    sys.argv = ["open_latest_summary.py", "--print", "--dir", str(sums_dir)]
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = mod.main()
        out = buf.getvalue()
        assert rc == 0
        assert latest.name in out
    finally:
        sys.argv = old_argv
