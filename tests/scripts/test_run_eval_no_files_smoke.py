from __future__ import annotations

import asyncio
import os
from pathlib import Path
import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.asyncio
async def test_run_eval_load_evaluation_items_no_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_eval = importlib.import_module("scripts.run_eval")
    # Pattern auf leeres Verzeichnis richten
    pattern = os.fspath(tmp_path / "*.jsonl")
    items = await run_eval.load_evaluation_items([pattern])
    assert isinstance(items, list)
    assert len(items) == 0
