from __future__ import annotations

import importlib
from types import SimpleNamespace

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_run_tests_main_mocks_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.import_module("scripts.run_tests")

    # Mock subprocess.run to avoid executing pytest; simulate return code 0
    calls: dict[str, object] = {}

    def fake_run(cmd, cwd=None):  # type: ignore[no-redef]
        calls["cmd"] = cmd
        calls["cwd"] = cwd
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(mod, "subprocess", SimpleNamespace(run=fake_run))

    rc = mod.main()
    assert rc == 0
    cmd = calls.get("cmd")
    assert isinstance(cmd, list)
    assert "-m" in cmd, "should invoke python -m pytest"
