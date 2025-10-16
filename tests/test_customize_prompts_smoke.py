from __future__ import annotations

import sys
import importlib
import types
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_customize_prompts_help_path(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    # Simuliere Aufruf ohne Argumente -> parser.print_help() und normaler Exit (kein SystemExit)
    monkeypatch.setenv("PYTHONWARNINGS", "ignore")

    # Sicherstellen, dass sys.argv nur das Skript enthält
    monkeypatch.setattr(sys, "argv", ["customize_prompts.py"])  # type: ignore[assignment]

    # Import und main() ausführen
    mod = importlib.import_module("scripts.customize_prompts")
    assert isinstance(mod, types.ModuleType)

    # Aufruf von main ohne Flags sollte nur Hilfe ausgeben und None zurückgeben
    result = mod.main()
    captured = capsys.readouterr()

    assert result is None
    # Hilfe-Text sollte enthalten sein
    assert "Prompt-Anpassungstool" in captured.out or "usage:" in captured.out.lower()
