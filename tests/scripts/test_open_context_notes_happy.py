from __future__ import annotations

import importlib
from pathlib import Path
import io
import contextlib
import types
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_open_context_notes_happy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.open_context_notes")

    target = tmp_path / "eval" / "config" / "context.local.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    # Stub settings to point to our temp path
    # Patch settings directly in the module under test so the reference matches
    monkeypatch.setattr(mod, "settings", types.SimpleNamespace(CONTEXT_NOTES_PATHS=[str(target)]), raising=False)

    # Prevent actually opening a file
    called: dict[str, str] = {}
    def _open_file(p: str) -> None:  # noqa: ANN001
        called["path"] = p
    monkeypatch.setattr(mod, "open_file", _open_file)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main()
    assert rc == 0
    out = buf.getvalue()
    assert "opening" in out
    assert called.get("path") == str(target)
    # File should exist and start with header
    assert target.exists()
    assert target.read_text(encoding="utf-8").startswith("# Kontext-Notizen")
