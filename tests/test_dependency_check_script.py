from __future__ import annotations

import io
import sys
import contextlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_dependency_check_runs_and_reports_basic_info() -> None:
    # Import als Modul und main() ausführen, stdout capturen
    import importlib
    mod = importlib.import_module("scripts.dependency_check")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod.main()
    out = buf.getvalue()
    # Erwartete Überschrift und einige Kern-Themen
    assert "Dependency Check" in out
    assert "run_eval" in out
    assert "Eval-Systemprompt" in out or "Eval-Systemprompt-Injektion" in out
    # Es darf nicht komplett leer sein
    assert len(out.strip()) > 10
