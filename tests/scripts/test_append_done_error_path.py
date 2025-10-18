from __future__ import annotations

import importlib
from pathlib import Path

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_append_done_invalid_args(tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.append_done")
    # Umleiten des LOG_PATH, um kein echtes File zu berühren
    setattr(mod, "LOG_PATH", str(tmp_path / "DONELOG.txt"))

    # Keine Argumente → 2
    assert mod.main([]) == 2
    # Leere Nachricht → 2
    assert mod.main([""]) == 2
