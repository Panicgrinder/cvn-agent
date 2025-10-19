from __future__ import annotations

import os
import importlib
import io
import contextlib
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_customize_unrestricted_prompt_updates_file(monkeypatch: pytest.MonkeyPatch, tmp_path: "os.PathLike[str]") -> None:
    mod = importlib.import_module("scripts.customize_prompts")

    tmp_root = os.fspath(tmp_path)
    app_core = os.path.join(tmp_root, "app", "core")
    os.makedirs(app_core, exist_ok=True)
    prompts_file = os.path.join(app_core, "prompts.py")
    with open(prompts_file, "w", encoding="utf-8") as f:
        f.write('UNRESTRICTED_SYSTEM_PROMPT = """ALT"""\n')

    monkeypatch.setattr(mod, "project_root", tmp_root, raising=False)
    monkeypatch.setattr(mod, "PROMPTS_FILE", prompts_file, raising=False)

    # simulate user entering two lines then EOF
    inputs = iter(["NEU-ZEILE-1", "NEU-ZEILE-2"])  # danach StopIteration -> EOFError simulieren
    def _input(prompt: str = "") -> str:
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError()
    monkeypatch.setattr("builtins.input", _input)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.customize_unrestricted_prompt()

    content = open(prompts_file, "r", encoding="utf-8").read()
    assert "NEU-ZEILE-1\nNEU-ZEILE-2" in content


@pytest.mark.scripts
@pytest.mark.unit
def test_customize_unrestricted_prompt_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch, tmp_path: "os.PathLike[str]") -> None:
    mod = importlib.import_module("scripts.customize_prompts")
    tmp_root = os.fspath(tmp_path)
    app_core = os.path.join(tmp_root, "app", "core")
    os.makedirs(app_core, exist_ok=True)
    prompts_file = os.path.join(app_core, "prompts.py")
    with open(prompts_file, "w", encoding="utf-8") as f:
        f.write('UNRESTRICTED_SYSTEM_PROMPT = """ALT-KONTENT"""\n')

    monkeypatch.setattr(mod, "project_root", tmp_root, raising=False)
    monkeypatch.setattr(mod, "PROMPTS_FILE", prompts_file, raising=False)

    def _interrupt(prompt: str = "") -> str:
        raise KeyboardInterrupt()
    monkeypatch.setattr("builtins.input", _interrupt)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.customize_unrestricted_prompt()

    # Datei sollte unverändert bleiben
    content = open(prompts_file, "r", encoding="utf-8").read()
    assert "ALT-KONTENT" in content
