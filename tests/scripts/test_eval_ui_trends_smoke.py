from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_eval_ui_meta_and_results_parsing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ui = importlib.import_module("scripts.eval_ui")
    run_eval = ui.run_eval

    res_dir = tmp_path / "eval" / "results"
    res_dir.mkdir(parents=True, exist_ok=True)
    res_path = res_dir / "results_20250101_1200.jsonl"

    with open(res_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": True, "timestamp": "2025-01-01T12:00:00Z", "overrides": {"model": "m"}, "enabled_checks": ["must_include"]}) + "\n")
        f.write(json.dumps({"item_id": "eval-001", "response": "ok", "checks_passed": {"must_include": True}, "success": True, "failed_checks": [], "duration_ms": 10}) + "\n")
        f.write(json.dumps({"item_id": "eval-002", "response": "bad", "checks_passed": {"must_include": False}, "success": False, "failed_checks": ["must_include"], "duration_ms": 12}) + "\n")

    monkeypatch.setattr(run_eval, "DEFAULT_RESULTS_DIR", os.fspath(res_dir), raising=False)

    meta = ui.load_run_meta(os.fspath(res_path))
    assert meta and meta.get("_meta") is True

    results = ui.load_results_from_file(os.fspath(res_path))
    assert results and len(results) == 2
