from __future__ import annotations

import importlib
from pathlib import Path
import json
import io
import contextlib
import types
import pytest
from typing import Any, Dict


@pytest.mark.scripts
@pytest.mark.unit
def test_curate_filters_exclude_all(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.curate_dataset_from_latest")

    res_dir = tmp_path / "eval" / "results"
    res_dir.mkdir(parents=True)
    res_file = res_dir / "results_20250101_0000.jsonl"
    res_file.write_text(json.dumps({"item_id":"eval-1","success":True,"response":"ok"})+"\n", encoding="utf-8")

    # Stub export to write a minimal record that will be filtered out by stringent filters
    exported = res_dir / "finetune" / "fin.jsonl"
    (res_dir / "finetune").mkdir(parents=True)

    async def _export(results_path: str, out_dir: str, format: str, include_failures: bool) -> Dict[str, Any]:  # noqa: ANN001
        p = exported
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"messages":[{"role":"user","content":"hi"},{"role":"assistant","content":"a"}]} )+"\n", encoding="utf-8")
        return {"ok": True, "out": str(p), "count": 1}

    def _prepare_pack(*_a: Any, **_k: Any) -> Dict[str, Any]:  # noqa: ANN001
        return {"ok": True, "train": "t", "val": "v", "counts": {}}

    monkeypatch.setattr(mod, "_export", types.SimpleNamespace(export_from_results=_export))
    monkeypatch.setattr(mod, "_prepare", types.SimpleNamespace(prepare_pack=_prepare_pack))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import sys
        sys.argv = [
            "curate_dataset_from_latest.py",
            "--results-dir", str(res_dir),
            "--format", "openai_chat",
            "--min-assistant-words", "100",  # unrealistisch hoch → filtert alles
            "--min-instr-cover", "1.0",
            "--require-list-min", "3",
        ]
        rc = mod.main()
    assert rc == 5
    out = buf.getvalue()
    assert "Alle Einträge wurden durch Filter ausgeschlossen" in out
