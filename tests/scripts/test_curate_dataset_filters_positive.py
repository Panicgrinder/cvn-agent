from __future__ import annotations

import importlib
from pathlib import Path
import json
import io
import contextlib
import types
from typing import Any, Dict
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_curate_filters_keep_one(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.curate_dataset_from_latest")

    # Arrange: results dir with a dummy results file so _latest_results finds something
    res_dir = tmp_path / "eval" / "results"
    res_dir.mkdir(parents=True)
    res_file = res_dir / "results_20250102_0000.jsonl"
    res_file.write_text("{}\n", encoding="utf-8")

    # Prepare an export path where the exporter will write JSONL
    fin_dir = res_dir / "finetune"
    fin_dir.mkdir(parents=True)
    exported = fin_dir / "fin.jsonl"

    # Stub exporter: writes a single record that satisfies filters
    async def _export(results_path: str, out_dir: str, format: str, include_failures: bool) -> Dict[str, Any]:  # noqa: ANN001
        rec = {
            "messages": [
                {"role": "user", "content": "Bitte liste Punkte auf"},
                {"role": "assistant", "content": "- Punkt eins\n- Punkt zwei"},
            ]
        }
        exported.write_text(json.dumps(rec) + "\n", encoding="utf-8")
        return {"ok": True, "out": str(exported), "count": 1}

    # Stub prepare: return OK
    def _prepare_pack(*_a: Any, **_k: Any) -> Dict[str, Any]:  # noqa: ANN001
        return {"ok": True, "train": str(fin_dir / "train.jsonl"), "val": str(fin_dir / "val.jsonl"), "counts": {"train": 1, "val": 0}}

    monkeypatch.setattr(mod, "_export", types.SimpleNamespace(export_from_results=_export))
    monkeypatch.setattr(mod, "_prepare", types.SimpleNamespace(prepare_pack=_prepare_pack))

    # Act: run with filters that the record passes
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import sys
        sys.argv = [
            "curate_dataset_from_latest.py",
            "--results-dir", str(res_dir),
            "--format", "openai_chat",
            "--min-assistant-words", "2",
            "--require-list-min", "1",
        ]
        rc = mod.main()

    # Assert return code and that export file still has one line
    assert rc == 0
    out = buf.getvalue()
    # Parse printed JSON report (full pretty JSON)
    report = json.loads(out)
    exp_path = Path(report["export"])  # type: ignore[index]
    assert exp_path.exists()
    content = exp_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) == 1
    obj = json.loads(content[0])
    assert any(m.get("role") == "assistant" for m in obj.get("messages", []))
