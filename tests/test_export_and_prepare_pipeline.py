from __future__ import annotations

import os
import json
import asyncio
from typing import Any, Dict

import pytest


def _write_results_jsonl(path: str) -> None:
    # Mini-Datei mit einem Meta-Header und einem erfolgreichen Ergebnis
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": True, "enabled_checks": ["must_include"], "timestamp": "20250101_1200"})+"\n")
        f.write(json.dumps({
            "item_id": "eval-demo-1",
            "response": "Antwort 1",
            "checks_passed": {"must_include": True},
            "success": True,
            "failed_checks": [],
            "source_file": "eval-21-40_fantasy_v1.0.jsonl",
            "source_package": "general",
            "duration_ms": 10
        }, ensure_ascii=False)+"\n")


def _write_min_dataset_jsonl(path: str) -> None:
    # Minimales Dataset mit der passenden item_id und user-Nachricht
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "id": "eval-demo-1",
            "messages": [
                {"role": "user", "content": "Sag hallo"}
            ],
            "checks": {"must_include": ["Antwort"]},
            "source_file": os.path.basename(path),
            "source_package": "general"
        }, ensure_ascii=False)+"\n")


@pytest.mark.scripts
@pytest.mark.unit
def test_export_openai_chat_and_prepare_pack(tmp_path: "os.PathLike[str]") -> None:
    # 1) Results-Datei erzeugen
    results_path = os.path.join(tmp_path, "results_20250101_1200.jsonl")
    _write_results_jsonl(results_path)

    # 2) Export (openai_chat) mit eigenen Patterns auf das temporäre Dataset
    dataset_path = os.path.join(tmp_path, "dataset.jsonl")
    _write_min_dataset_jsonl(dataset_path)
    from scripts import export_finetune as exporter
    out = asyncio.run(exporter.export_from_results(
        results_path,
        out_dir=str(tmp_path),
        format="openai_chat",
        include_failures=False,
        patterns=[dataset_path]
    ))
    assert out.get("ok")
    exported = str(out.get("out"))
    assert os.path.exists(exported)

    # 3) Prepare-Pack (Train/Val)
    from scripts import prepare_finetune_pack as prep
    res: Dict[str, Any] = prep.prepare_pack(exported, out_dir=str(tmp_path), format="openai_chat", train_ratio=0.5, seed=1, min_output_chars=1)
    assert res.get("ok")
    assert os.path.exists(str(res.get("train")))
    assert os.path.exists(str(res.get("val")))
