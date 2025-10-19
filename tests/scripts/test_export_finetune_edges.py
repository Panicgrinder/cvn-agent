from __future__ import annotations

import os
import json
import asyncio
from typing import Any, Dict

import pytest


def _write_mixed_results(path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": True}) + "\n")
        # Ungültige Zeile (kein JSON)
        f.write("not-a-json-line\n")
        # Ungültiges JSON, aber nicht-Objekt -> wird verworfen
        f.write(json.dumps([1, 2, 3]) + "\n")
        # Fehlgeschlagenes Ergebnis (wird standardmäßig gefiltert)
        f.write(json.dumps({
            "item_id": "item-err",
            "response": "",
            "checks_passed": {"must_include": False},
            "success": False,
            "failed_checks": ["must_include"],
            "source_file": "eval-x.jsonl",
            "source_package": "general"
        }, ensure_ascii=False) + "\n")
        # Erfolgreiches Ergebnis
        f.write(json.dumps({
            "item_id": "item-ok",
            "response": "Antwort",
            "checks_passed": {"must_include": True},
            "success": True,
            "failed_checks": [],
            "source_file": "eval-x.jsonl",
            "source_package": "general"
        }, ensure_ascii=False) + "\n")


def _write_min_dataset(path: str, item_id: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "id": item_id,
            "messages": [{"role": "user", "content": "Sag hallo"}],
            "source_package": "general"
        }, ensure_ascii=False) + "\n")


@pytest.mark.scripts
@pytest.mark.unit
def test_export_filters_failures_by_default(tmp_path: "os.PathLike[str]") -> None:
    from scripts import export_finetune as exporter
    results = os.path.join(tmp_path, "results.jsonl")
    _write_mixed_results(results)
    dataset = os.path.join(tmp_path, "eval-x.jsonl")
    _write_min_dataset(dataset, "item-ok")

    out = asyncio.run(exporter.export_from_results(results, out_dir=str(tmp_path), format="alpaca", include_failures=False, patterns=[dataset]))
    assert out.get("ok")
    out_path = str(out.get("out"))
    with open(out_path, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    # Nur der erfolgreiche Eintrag wird exportiert
    assert len(lines) == 1
    assert lines[0]["meta"]["id"] == "item-ok"


@pytest.mark.scripts
@pytest.mark.unit
def test_export_includes_failures_when_requested(tmp_path: "os.PathLike[str]") -> None:
    from scripts import export_finetune as exporter
    results = os.path.join(tmp_path, "results.jsonl")
    _write_mixed_results(results)
    dataset_ok = os.path.join(tmp_path, "eval-x-ok.jsonl")
    dataset_err = os.path.join(tmp_path, "eval-x-err.jsonl")
    _write_min_dataset(dataset_ok, "item-ok")
    _write_min_dataset(dataset_err, "item-err")

    out = asyncio.run(exporter.export_from_results(results, out_dir=str(tmp_path), format="openai_chat", include_failures=True, patterns=[dataset_ok, dataset_err]))
    assert out.get("ok")
    out_path = str(out.get("out"))
    with open(out_path, "r", encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    # Beide Einträge sollten vorhanden sein (ok + err), Reihenfolge egal
    metas = [r.get("meta", {}) for r in rows]
    ids = {m.get("id") for m in metas}
    assert {"item-ok", "item-err"}.issubset(ids)
