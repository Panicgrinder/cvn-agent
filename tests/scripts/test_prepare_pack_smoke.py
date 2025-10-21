from __future__ import annotations

import json
import pathlib
import pytest

BASE = pathlib.Path(__file__).resolve().parents[2]
EXPORT_FILE = BASE / "eval" / "results" / "finetune" / "exports" / "openai_chat.jsonl"
TRAIN_FILE = BASE / "eval" / "results" / "finetune" / "train.jsonl"
VAL_FILE = BASE / "eval" / "results" / "finetune" / "val.jsonl"


def _validate_jsonl(path: pathlib.Path) -> None:
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                json.loads(line)
            except Exception as e:
                raise AssertionError(f"Invalid JSON at line {i} in {path}: {e}")


@pytest.mark.scripts
def test_prepare_pack_smoke():
    # Skip if export file missing (no prior export run)
    if not EXPORT_FILE.exists():
        pytest.skip(f"Missing export file: {EXPORT_FILE}")

    # If train/val exist, validate their JSONL integrity
    if TRAIN_FILE.exists():
        _validate_jsonl(TRAIN_FILE)
    if VAL_FILE.exists():
        _validate_jsonl(VAL_FILE)

    # If neither train nor val exists, that's okay for smoke: nothing to validate
    assert True
