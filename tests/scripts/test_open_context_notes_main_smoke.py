from __future__ import annotations

import json
import os
from pathlib import Path
import importlib
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_open_context_notes_main_with_mock(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.open_context_notes")

    # env override: enable and set paths to tmp
    cfg_path = tmp_path / "eval" / "config" / "context.local.md"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("CONTEXT_NOTES_ENABLED", "true")
    monkeypatch.setenv("CONTEXT_NOTES_PATHS", json.dumps([os.fspath(cfg_path)]))

    # reload settings and module to pick up env
    import importlib as _imp
    _imp.reload(_imp.import_module("app.core.settings"))
    _imp.reload(mod)

    opened: list[str] = []
    def _fake_open(p: str) -> None:
        opened.append(p)

    monkeypatch.setattr(mod, "open_file", _fake_open)

    rc = mod.main()
    assert rc in (0, 1)
    assert opened, "open_file wurde nicht aufgerufen"
