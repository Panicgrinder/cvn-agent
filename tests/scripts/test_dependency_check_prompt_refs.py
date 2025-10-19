from __future__ import annotations

import io
import contextlib
import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_dependency_check_prompt_reference_scan_runs() -> None:
    mod = importlib.import_module("scripts.dependency_check")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        # Direkt die spezifische Prüfroutine ausführen, um schneller zu sein
        mod.check_prompt_files_not_referenced()
    out = buf.getvalue()
    # Erwartet, dass eine Aussage getroffen wird (OK oder WARN) – aber kein Crash
    assert "Historische Prompt-Datei" in out or "existiert nicht" in out
