from __future__ import annotations

from pathlib import Path
import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_open_latest_summary_opened(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.open_latest_summary")

    sums_dir = tmp_path / "eval" / "results" / "summaries"
    sums_dir.mkdir(parents=True, exist_ok=True)
    target = sums_dir / "summary_ALL_20251231.md"
    target.write_text("hello", encoding="utf-8")

    # Patch Defaults
    monkeypatch.setattr(mod, "SUMMARY_DIR", sums_dir)
    monkeypatch.setattr(mod, "SUMMARY_GLOB", "summary_ALL_*.md")

    opened: list[str] = []
    def _fake_open(path: Path) -> None:
        opened.append(str(path))

    monkeypatch.setattr(mod, "open_file", _fake_open)
    import sys
    argv_bak = sys.argv
    try:
        sys.argv = ["open_latest_summary.py", "--dir", str(sums_dir)]
        # Aufruf über __main__-Guard simulieren
        with pytest.raises(SystemExit):
            mod.__main__  # type: ignore[attr-defined]
    except AttributeError:
        # Fallback: direkter main()-Call ohne argv
        rc = mod.main()
        assert rc == 0
    finally:
        sys.argv = argv_bak
    assert opened and target.name in opened[0]
