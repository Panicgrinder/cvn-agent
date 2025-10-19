from __future__ import annotations

import os
import json
import asyncio
import importlib
from pathlib import Path
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_export_finetune_no_rows_returns_error(tmp_path: Path) -> None:
    from scripts import export_finetune as exporter
    res = tmp_path / "empty_results.jsonl"
    res.write_text("\n", encoding="utf-8")
    out = asyncio.run(exporter.export_from_results(str(res), out_dir=str(tmp_path), format="alpaca", include_failures=False, patterns=[str(tmp_path/"none.jsonl")]))
    assert out.get("ok") is False
    assert "Keine Ergebnisse" in str(out.get("error"))


@pytest.mark.scripts
@pytest.mark.unit
def test_rerun_failed_missing_items_in_datasets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.import_module("scripts.rerun_failed")
    # Ergebnisse mit fehlgeschlagener ID
    results_dir = tmp_path / "eval" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    res = results_dir / "results_20250101_1200.jsonl"
    with open(res, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": True}) + "\n")
        f.write(json.dumps({"item_id": "eval-404", "success": False, "failed_checks": ["x"]}) + "\n")

    # DATASETS_DIR leer lassen -> keine Zuordnung
    monkeypatch.setattr(mod, "RESULTS_DIR", os.fspath(results_dir), raising=False)
    monkeypatch.setattr(mod, "DATASETS_DIR", os.fspath(tmp_path/"eval"/"datasets"), raising=False)

    rc = mod.main()
    assert rc == 2
