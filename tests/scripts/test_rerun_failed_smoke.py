from __future__ import annotations

import json
import os
from pathlib import Path
import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_rerun_failed_creates_tmp_dataset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Simulierte Projektstruktur
    proj = tmp_path
    ds_dir = proj / "eval" / "datasets"
    res_dir = proj / "eval" / "results"
    ds_dir.mkdir(parents=True, exist_ok=True)
    res_dir.mkdir(parents=True, exist_ok=True)

    # Dataset mit ids
    with open(ds_dir / "eval-foo.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({"id": "eval-001", "messages": [{"role": "user", "content": "a"}]}) + "\n")
        f.write(json.dumps({"id": "eval-002", "messages": [{"role": "user", "content": "b"}]}) + "\n")

    # Results mit einem Fehler (für 001)
    res_path = res_dir / "results_20250101_1200.jsonl"
    with open(res_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": True}) + "\n")
        f.write(json.dumps({"item_id": "eval-001", "success": False, "error": "boom"}) + "\n")

    mod = importlib.import_module("scripts.rerun_failed")
    # Patch Projektpfade
    monkeypatch.setattr(mod, "PROJECT_ROOT", os.fspath(proj))
    monkeypatch.setattr(mod, "DATASETS_DIR", os.fspath(ds_dir))
    monkeypatch.setattr(mod, "RESULTS_DIR", os.fspath(res_dir))
    monkeypatch.setattr(mod, "TMP_DIR", os.fspath(res_dir / "tmp"))

    rc = mod.main()
    assert rc == 0
    tmp = res_dir / "tmp"
    files = list(tmp.glob("rerun_*.jsonl"))
    assert files, "rerun_*.jsonl nicht erstellt"
