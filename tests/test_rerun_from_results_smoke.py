from __future__ import annotations

import os
import json
import asyncio
from typing import Dict

import pytest


def _write_results_with_meta(path: str, item_id: str, dataset_basename: str) -> None:
    meta: Dict[str, object] = {
        "_meta": True,
        "enabled_checks": ["must_include"],
        "eval_mode": True,
        "asgi": True,  # ASGI-Transport verwenden
        "api_url": "http://localhost:8000/chat",
        "overrides": {"model": "dummy-model", "temperature": 0.2},
        "patterns": [dataset_basename],  # wird vom Loader relativ zur DEFAULT_DATASET_DIR aufgelöst
    }
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(meta) + "\n")
        f.write(json.dumps({
            "item_id": item_id,
            "response": "Antwort",
            "checks_passed": {"must_include": True},
            "success": False,  # als fehlgeschlagen markieren, damit only_failed greift
            "failed_checks": ["must_include"],
            "source_file": dataset_basename,
            "source_package": "general",
        }, ensure_ascii=False) + "\n")


@pytest.mark.scripts
def test_rerun_from_results_smoke(tmp_path: "os.PathLike[str]") -> None:
    # Mini-Dataset im eval/datasets-Layout
    from scripts import rerun_from_results as rfr
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(rfr.__file__)))
    datasets_dir = os.path.join(project_root, "eval", "datasets")
    os.makedirs(datasets_dir, exist_ok=True)
    dataset_basename = "eval-smoke.jsonl"
    dataset_path = os.path.join(datasets_dir, dataset_basename)
    item_id = "eval-smoke-1"
    with open(dataset_path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "id": item_id,
            "messages": [
                {"role": "user", "content": "Sag hallo"}
            ],
            "source_package": "general"
        }, ensure_ascii=False) + "\n")

    # Results-Datei mit Meta erzeugen
    results_path = os.path.join(tmp_path, "results_smoke.jsonl")
    _write_results_with_meta(results_path, item_id, dataset_basename)

    # Rerun ausführen (only_failed=True default)
    out = asyncio.run(rfr.rerun_from_results(results_path))
    assert out.get("ok") is True
    out_path = str(out.get("out"))
    assert os.path.exists(out_path)
