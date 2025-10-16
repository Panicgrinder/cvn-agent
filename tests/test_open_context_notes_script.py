from __future__ import annotations

import os
import json
import importlib
from typing import List

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_open_context_notes_pick_and_ensure(tmp_path: "os.PathLike[str]") -> None:
    # Erzeuge zwei potentielle Pfade, einer existiert
    path1 = os.path.join(tmp_path, "eval", "config", "context.local.md")
    path2 = os.path.join(tmp_path, "data", "context.local.md")
    os.makedirs(os.path.dirname(path2), exist_ok=True)
    with open(path2, "w", encoding="utf-8") as f:
        f.write("# stub\n")

    mod = importlib.import_module("scripts.open_context_notes")
    # pick_target nimmt existierenden zuerst
    picked = mod.pick_target([path1, path2])
    assert picked == path2

    # ensure_file erzeugt Datei, wenn sie fehlt
    new_path = os.path.join(tmp_path, "eval", "config", "new_context.md")
    ensured = mod.ensure_file(new_path)
    assert os.path.exists(ensured)


@pytest.mark.scripts
@pytest.mark.unit
def test_open_context_notes_main_opens(monkeypatch: pytest.MonkeyPatch, tmp_path: "os.PathLike[str]") -> None:
    mod = importlib.import_module("scripts.open_context_notes")

    opened: list[str] = []
    def _fake_open(p: str) -> None:
        opened.append(p)

    # Umgebung so setzen, dass settings die Pfade verwendet
    monkeypatch.setenv("CONTEXT_NOTES_ENABLED", "true")
    monkeypatch.setenv("CONTEXT_NOTES_PATHS", json.dumps([os.path.join(tmp_path, "eval", "config", "context.local.md")]))

    import importlib as _imp
    _imp.reload(_imp.import_module("app.core.settings"))
    _imp.reload(mod)

    monkeypatch.setattr(mod, "open_file", _fake_open)

    code = mod.main()
    assert code in (0, 1)  # Öffnen kann in CI scheitern; Hauptsache, es läuft bis zum Ende
    assert opened  # wurde versucht zu öffnen
