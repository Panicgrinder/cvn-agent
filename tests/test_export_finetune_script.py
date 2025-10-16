from __future__ import annotations

import os
import json
import asyncio
from typing import Any, Dict

import pytest


def _write_results(path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": True}) + "\n")
        f.write(json.dumps({
            "item_id": "item-1",
            "response": "Antwort",
            "checks_passed": {"must_include": True},
            "success": True,
            "failed_checks": [],
            "source_file": "eval-01.jsonl",
            "source_package": "general"
        }, ensure_ascii=False) + "\n")


@pytest.mark.scripts
@pytest.mark.unit
def test_export_finetune_openai_chat_with_patterns(tmp_path: "os.PathLike[str]") -> None:
    # Mini Dataset
    dataset = os.path.join(tmp_path, "eval-01.jsonl")
    with open(dataset, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "id": "item-1",
            "messages": [
                {"role": "user", "content": "Sag hallo"}
            ],
            "source_package": "general"
        }, ensure_ascii=False) + "\n")

    results = os.path.join(tmp_path, "results_20250101_1200.jsonl")
    _write_results(results)

    # Export mit Patterns (nur unser temp dataset) und Format openai_chat
    from scripts import export_finetune as exporter
    ds_pattern = dataset.replace('\\', '/')
    out = asyncio.run(exporter.export_from_results(results_path=results, out_dir=str(tmp_path), format="openai_chat", include_failures=False, patterns=[ds_pattern]))
    assert out.get("ok")
    out_path = str(out.get("out"))
    assert os.path.exists(out_path)
    with open(out_path, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    assert len(lines) == 1
    rec = lines[0]
    assert isinstance(rec.get("messages"), list)
    assert rec.get("meta", {}).get("id") == "item-1"
