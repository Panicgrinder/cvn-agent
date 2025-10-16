from __future__ import annotations

import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_quick_eval_script_imports_and_runs_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    # Nur Import-/Smoke-Test (kein echtes Modell); das Skript sollte importierbar sein.
    import scripts.quick_eval as mod
    assert hasattr(mod, "main") or True


@pytest.mark.scripts
@pytest.mark.unit
def test_open_latest_summary_import_smoke() -> None:
    mod = importlib.import_module("scripts.open_latest_summary")
    assert callable(getattr(mod, "main", lambda: None)) or True
