from __future__ import annotations

import os
import json
import importlib
from pathlib import Path

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_rerun_failed_only_success_returns_zero(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Ergebnisse: nur erfolgreich
    results_dir = tmp_path / "eval" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    res_path = results_dir / "results_20250101_1200.jsonl"
    with open(res_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": True}) + "\n")
        f.write(json.dumps({
            "item_id": "eval-1",
            "success": True,
            "failed_checks": [],
            "response": "ok"
        }) + "\n")

    mod = importlib.import_module("scripts.rerun_failed")

    # Project-Pfade umbiegen
    monkeypatch.setattr(mod, "RESULTS_DIR", os.fspath(results_dir), raising=False)
    monkeypatch.setattr(mod, "DATASETS_DIR", os.fspath(tmp_path / "eval" / "datasets"), raising=False)

    rc = mod.main()
    assert rc == 0
