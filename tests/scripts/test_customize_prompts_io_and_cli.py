from __future__ import annotations

import os
import io
import json
import importlib
from typing import Any

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_customize_prompts_create_rules_and_io(monkeypatch: pytest.MonkeyPatch, tmp_path: "os.PathLike[str]") -> None:
    # Modul laden und auf temporäres project_root umbiegen
    mod = importlib.import_module("scripts.customize_prompts")

    # tmp project structure
    tmp_root = os.fspath(tmp_path)
    app_core = os.path.join(tmp_root, "app", "core")
    os.makedirs(app_core, exist_ok=True)

    # prompts.py anlegen und PROMPTS_FILE/Pfad im Modul überschreiben
    prompts_file = os.path.join(app_core, "prompts.py")
    initial = 'UNRESTRICTED_SYSTEM_PROMPT = """ALT"""\n'
    with open(prompts_file, "w", encoding="utf-8") as f:
        f.write(initial)

    monkeypatch.setattr(mod, "project_root", tmp_root, raising=False)
    monkeypatch.setattr(mod, "PROMPTS_FILE", prompts_file, raising=False)

    # read_prompts / write_prompts
    assert mod.read_prompts().strip() == initial.strip()
    mod.write_prompts('UNRESTRICTED_SYSTEM_PROMPT = """NEU"""\n')
    assert "NEU" in mod.read_prompts()

    # create_content_rules: simulate user input
    inputs = iter(["Beispiele: erlaubt", "Offtopic: verboten", "fertig"])  # zwei Regeln + fertig
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    # capture stdout to ensure it runs through
    buf = io.StringIO()
    import contextlib
    with contextlib.redirect_stdout(buf):
        mod.create_content_rules()

    rules_file = os.path.join(app_core, "content_rules.json")
    assert os.path.exists(rules_file)
    with open(rules_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("Beispiele") is True
    assert data.get("Offtopic") is False


@pytest.mark.scripts
@pytest.mark.unit
def test_customize_prompts_main_help(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.import_module("scripts.customize_prompts")
    # Rufe ohne Argumente auf, erwartet: help-Ausgabe, kein Crash
    import sys
    argv_backup = sys.argv[:]
    try:
        sys.argv = ["customize_prompts.py"]
        mod.main()
    finally:
        sys.argv = argv_backup
