from __future__ import annotations

import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_run_tests_returns_127_on_missing_pytest(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.import_module("scripts.run_tests")

    class _Subproc:
        def run(self, *args, **kwargs):  # type: ignore[no-redef]
            raise FileNotFoundError("pytest not found")

    monkeypatch.setattr(mod, "subprocess", _Subproc())
    rc = mod.main()
    assert rc == 127
