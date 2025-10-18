from __future__ import annotations

import os
from pathlib import Path
import importlib
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_map_reduce_summary_heuristic_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Minimaler Input: zwei kleine Dateien
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "a.py").write_text("print('a')\n", encoding="utf-8")
    (src_dir / "b.py").write_text("# b\n", encoding="utf-8")

    mod = importlib.import_module("scripts.map_reduce_summary")

    # SCOPES um temporären Eintrag erweitern
    mod.SCOPES["tmp"] = os.fspath(src_dir)  # type: ignore[attr-defined]

    # Führe die Hauptfunktion mit Scope-Namen, erwarte Exit 0
    code = mod.main(["--scopes", "tmp", "--max-files", "2", "--out-dir", os.fspath(tmp_path)])
    assert isinstance(code, int) and code == 0
    # Erwartete Dateien: summary_<ts>_tmp.md und summary_ALL_<ts>.md im out-dir
    files = list(tmp_path.glob("summary_*_tmp.md"))
    merged = list(tmp_path.glob("summary_ALL_*.md"))
    assert files and merged
