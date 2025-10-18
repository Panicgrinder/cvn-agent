from __future__ import annotations

import os
from pathlib import Path
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_append_done_writes_line(tmp_path: Path) -> None:
    # Import hier, damit wir Konstanten danach patchen können
    import importlib

    mod = importlib.import_module("scripts.append_done")

    # Patch: schreibe in temporäre Datei und stabiler Autor
    log_path = os.fspath(tmp_path / "DONELOG.txt")
    setattr(mod, "LOG_PATH", log_path)
    setattr(mod, "get_author", lambda: "tester")  # vermeidet git-Aufruf

    rc = mod.main(["Kurzbeschreibung Testeintrag"])  # type: ignore[arg-type]
    assert rc == 0

    assert os.path.exists(log_path)
    content = open(log_path, "r", encoding="utf-8").read().strip()
    # Format: ts | author | msg
    assert "tester" in content
    assert "Kurzbeschreibung Testeintrag" in content
