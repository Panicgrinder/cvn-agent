from __future__ import annotations

import os
import json
import asyncio
from typing import Any, Dict

import pytest


def _write_results(path: str, item_id: str, src_file_basename: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": True, "enabled_checks": ["must_include"], "timestamp": "20250101_1200"}) + "\n")
        f.write(json.dumps({
            "item_id": item_id,
            "response": "Antwort",
            "checks_passed": {"must_include": True},
            "success": True,
            "failed_checks": [],
            "source_file": src_file_basename,
            "source_package": "general"
        }, ensure_ascii=False) + "\n")


def _write_dataset(path: str, item_id: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "id": item_id,
            "messages": [
                {"role": "user", "content": "Sag hallo"},
                {"role": "assistant", "content": "Hi!"}
            ],
            "source_package": "general"
        }, ensure_ascii=False) + "\n")


@pytest.mark.scripts
@pytest.mark.unit
def test_export_alpaca_and_then_prepare_pack(tmp_path: "os.PathLike[str]") -> None:
    item_id = "eval-demo-3"
    results_path = os.path.join(tmp_path, "results_20250101_1200.jsonl")
    dataset_path = os.path.join(tmp_path, "eval-demo.jsonl")

    _write_dataset(dataset_path, item_id)
    _write_results(results_path, item_id, os.path.basename(dataset_path))

    # Export alpaca
    from scripts import export_finetune as exporter
    out = asyncio.run(exporter.export_from_results(
        results_path=results_path,
        out_dir=str(tmp_path),
        format="alpaca",
        include_failures=False,
        patterns=[dataset_path.replace('\\', '/')],
    ))
    assert out.get("ok")
    alpaca_path = str(out.get("out"))
    assert os.path.exists(alpaca_path)

    # Prepare (alpaca)
    from scripts import prepare_finetune_pack as prep
    res: Dict[str, Any] = prep.prepare_pack(alpaca_path, out_dir=str(tmp_path), format="alpaca", train_ratio=0.5, seed=1, min_output_chars=1)
    assert res.get("ok")
    assert os.path.exists(str(res.get("train")))
    assert os.path.exists(str(res.get("val")))
