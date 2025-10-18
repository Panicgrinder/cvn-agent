from __future__ import annotations

from pathlib import Path
import importlib
import os

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_rerun_failed_no_results(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.import_module("scripts.rerun_failed")

    proj = tmp_path
    ds_dir = proj / "eval" / "datasets"
    res_dir = proj / "eval" / "results"
    ds_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(mod, "PROJECT_ROOT", os.fspath(proj))
    monkeypatch.setattr(mod, "DATASETS_DIR", os.fspath(ds_dir))
    monkeypatch.setattr(mod, "RESULTS_DIR", os.fspath(res_dir))
    monkeypatch.setattr(mod, "TMP_DIR", os.fspath(res_dir / "tmp"))

    rc = mod.main()
    assert rc == 1
