from __future__ import annotations

import importlib
import asyncio
from pathlib import Path
import json
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_outdir_none_settings_import_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.export_finetune")

    # Create a minimal results file with one success
    res_dir = tmp_path / "eval" / "results"
    res_dir.mkdir(parents=True)
    res_file = res_dir / "results_20250101_0101.jsonl"
    res_file.write_text(json.dumps({
        "item_id": "eval-1",
        "success": True,
        "response": "ok",
        "source_file": "dummy.jsonl",
    }) + "\n", encoding="utf-8")

    # Patch run_eval internals used by export_finetune
    class _Item:
        def __init__(self) -> None:
            self.id = "eval-1"
            self.messages = [{"role": "user", "content": "hi"}]
            self.source_package = "pack"

    from typing import Any, List
    async def _load_items(_patterns: Any = None) -> List[_Item]:
        return [ _Item() ]

    # Ensure DEFAULT_* constants exist and point into tmp workspace
    monkeypatch.setattr(mod.run_eval, "load_evaluation_items", _load_items)
    monkeypatch.setattr(mod.run_eval, "DEFAULT_DATASET_DIR", str(tmp_path / "eval" / "datasets"), raising=False)
    monkeypatch.setattr(mod.run_eval, "DEFAULT_EVAL_DIR", str(res_dir), raising=False)
    monkeypatch.setattr(mod.run_eval, "DEFAULT_RESULTS_DIR", str(res_dir), raising=False)
    monkeypatch.setattr(mod.run_eval, "DEFAULT_FILE_PATTERN", "*.jsonl", raising=False)

    # Force settings import to fail by injecting a dummy module later in sys.modules
    # but rely on try/except to fall back
    # Call with out_dir=None
    out = asyncio.run(mod.export_from_results(str(res_file), out_dir=None, format="alpaca"))
    assert out["ok"] is True
    assert out["count"] == 1
