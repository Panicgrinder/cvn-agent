from __future__ import annotations

import os
import json
import asyncio
from typing import Any, Dict

import pytest


def _write_results_single(path: str, item_id: str, success: bool = True, response: str = "OK") -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"_meta": True}) + "\n")
        f.write(json.dumps({
            "item_id": item_id,
            "response": response,
            "checks_passed": {"must_include": success},
            "success": success,
            "failed_checks": ([] if success else ["must_include"]),
            "source_file": "eval-x.jsonl",
            "source_package": "general"
        }, ensure_ascii=False) + "\n")


def _write_dataset_messages(path: str, item_id: str, messages: list[dict[str, str]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "id": item_id,
            "messages": messages,
            "source_package": "general"
        }, ensure_ascii=False) + "\n")


@pytest.mark.scripts
@pytest.mark.unit
def test_export_alpaca_instruction_and_input_split(tmp_path: "os.PathLike[str]") -> None:
    from scripts import export_finetune as exporter

    # Dataset mit mehreren Nachrichten: erste user = instruction, Rest wird input
    dataset = os.path.join(tmp_path, "ds.jsonl")
    messages = [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "U1"},
        {"role": "assistant", "content": "A1"},
        {"role": "user", "content": "U2"},
    ]
    _write_dataset_messages(dataset, "item-1", messages)
    results = os.path.join(tmp_path, "res.jsonl")
    _write_results_single(results, "item-1", success=True, response="R1")

    out = asyncio.run(exporter.export_from_results(results, out_dir=str(tmp_path), format="alpaca", include_failures=False, patterns=[dataset]))
    assert out.get("ok")
    out_path = str(out.get("out"))
    with open(out_path, "r", encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    assert len(rows) == 1
    rec = rows[0]
    assert rec.get("instruction") == "U1"
    # input sammelt restliche Inhalte (ohne erste user-Nachricht)
    assert "U2" in rec.get("input", "") or "A1" in rec.get("input", "")
    assert rec.get("output") == "R1"


@pytest.mark.scripts
@pytest.mark.unit
def test_export_out_dir_none_uses_settings_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: "os.PathLike[str]") -> None:
    from scripts import export_finetune as exporter
    # Stelle settings so ein, dass EVAL_RESULTS_DIR auf einen temporären Unterpfad zeigt
    import app.core.settings as settings_mod
    monkeypatch.setattr(settings_mod.settings, "EVAL_RESULTS_DIR", os.path.join("eval", "results", "tmp-export"), raising=False)

    ds = os.path.join(tmp_path, "d.jsonl")
    _write_dataset_messages(ds, "item-2", [{"role": "user", "content": "X"}])
    res = os.path.join(tmp_path, "r.jsonl")
    _write_results_single(res, "item-2", success=True, response="R2")

    out = asyncio.run(exporter.export_from_results(res, out_dir=None, format="alpaca", include_failures=False, patterns=[ds]))
    assert out.get("ok")
    out_path = str(out.get("out"))
    # sollte innerhalb des projekt-root eval/results/tmp-export landen
    assert "eval" in out_path.replace("\\", "/") and "tmp-export" in out_path.replace("\\", "/")


@pytest.mark.scripts
@pytest.mark.unit
def test_export_skips_unmapped_item(tmp_path: "os.PathLike[str]") -> None:
    from scripts import export_finetune as exporter
    # Ergebnis referenziert nicht existierendes Item
    res = os.path.join(tmp_path, "r.jsonl")
    _write_results_single(res, "missing-id", success=True, response="R3")
    out = asyncio.run(exporter.export_from_results(res, out_dir=str(tmp_path), format="alpaca", include_failures=True, patterns=[os.path.join(tmp_path, "empty.jsonl")]))
    assert out.get("ok")
    assert int(out.get("count", -1)) == 0
    out_path = str(out.get("out"))
    with open(out_path, "r", encoding="utf-8") as f:
        lines = [l for l in f if l.strip()]
    assert len(lines) == 0
