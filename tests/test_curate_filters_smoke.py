from __future__ import annotations

import io
import json
from types import SimpleNamespace
from pathlib import Path
from typing import Any, Dict

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_curation_filters_reduce_records(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    results_dir = tmp_path / "eval" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    results_file = results_dir / "results_20250101_0000.jsonl"
    results_file.write_text(
        "\n".join([
            json.dumps({"item_id": "eval-1", "success": True, "response": "kurz", "failed_checks": []}),
            json.dumps({"item_id": "eval-2", "success": True, "response": "antwort mit vielen worten und listen-\n- punkt eins\n- punkt zwei", "failed_checks": []}),
        ]),
        encoding="utf-8"
    )

    exported = results_dir / "finetune" / "finetune_openai_chat_results_20250101_0000_20250101_0101.jsonl"
    exported.parent.mkdir(parents=True, exist_ok=True)
    exported.write_text(
        "\n".join([
            json.dumps({
                "messages": [
                    {"role": "user", "content": "instr beispiel"},
                    {"role": "assistant", "content": "kurz"}
                ]
            }),
            json.dumps({
                "messages": [
                    {"role": "user", "content": "instr beispiel"},
                    {"role": "assistant", "content": "antwort mit vielen worten und listen-\n- punkt eins\n- punkt zwei"}
                ]
            })
        ]),
        encoding="utf-8"
    )

    async def fake_export(*_a: Any, **_k: Any) -> Dict[str, Any]:
        return {"ok": True, "out": str(exported), "count": 2}

    def fake_prepare(src_path: str, *_, **__) -> Dict[str, Any]:  # type: ignore[override]
        return {"ok": True, "train": str(exported) + "_train.jsonl", "val": str(exported) + "_val.jsonl", "counts": {"train": 1, "val": 1, "total": 1}}

    import importlib, sys
    mod = importlib.import_module("scripts.curate_dataset_from_latest")
    monkeypatch.setattr(sys, "argv", [
        "curate_dataset_from_latest.py",
        "--results-dir", str(results_dir),
        "--format", "openai_chat",
        "--min-assistant-words", "3",
        "--require-list-min", "2",
    ])
    monkeypatch.setattr(mod, "_export", SimpleNamespace(export_from_results=fake_export))
    monkeypatch.setattr(mod, "_prepare", SimpleNamespace(prepare_pack=fake_prepare))

    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main()
    assert rc == 0
    out = json.loads(buf.getvalue())
    assert out.get("ok") is True
