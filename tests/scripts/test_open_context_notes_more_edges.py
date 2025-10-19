from __future__ import annotations

import os
import json
import importlib
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_open_context_notes_open_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: "os.PathLike[str]") -> None:
    mod = importlib.import_module("scripts.open_context_notes")

    # Zielpfad vorgeben über ENV settings
    monkeypatch.setenv("CONTEXT_NOTES_ENABLED", "true")
    monkeypatch.setenv("CONTEXT_NOTES_PATHS", json.dumps([os.path.join(tmp_path, "eval", "config", "context.local.md")]))

    import importlib as _imp
    _imp.reload(_imp.import_module("app.core.settings"))
    _imp.reload(mod)

    # open_file schlägt fehl -> main() soll 1 zurückgeben
    def _raise(path: str) -> None:
        raise RuntimeError("öffnen fehlgeschlagen")

    monkeypatch.setattr(mod, "open_file", _raise)
    code = mod.main()
    assert code == 1


@pytest.mark.scripts
@pytest.mark.unit
def test_open_context_notes_ensure_with_sample(tmp_path: "os.PathLike[str]") -> None:
    mod = importlib.import_module("scripts.open_context_notes")
    target = os.path.join(tmp_path, "eval", "config", "ctx.md")
    sample = os.path.join(os.path.dirname(target), "context.local.sample.md")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(sample, "w", encoding="utf-8") as f:
        f.write("SAMPLE-CONTENT")

    out_path = mod.ensure_file(target)
    assert os.path.exists(out_path)
    with open(out_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "SAMPLE-CONTENT" in content
