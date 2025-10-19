from __future__ import annotations

import importlib
from pathlib import Path
import json
import io
import contextlib
import types
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_curate_minimal_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.curate_dataset_from_latest")

    res_dir = tmp_path / "eval" / "results"
    res_dir.mkdir(parents=True)
    res_file = res_dir / "results_20250101_0000.jsonl"
    res_file.write_text(json.dumps({"item_id":"eval-1","success":True,"response":"ok"})+"\n", encoding="utf-8")

    # Stub export and prepare modules used by the script
    exp_out = str(res_dir / "finetune" / "fin.jsonl")
    (res_dir / "finetune").mkdir(parents=True)

    from typing import Dict, Any
    async def _export(results_path: str, out_dir: str, format: str, include_failures: bool) -> Dict[str, Any]:  # noqa: ANN001
        # write a tiny exported file for prepare step
        p = Path(exp_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"messages":[{"role":"user","content":"q"},{"role":"assistant","content":"a"}]} )+"\n", encoding="utf-8")
        return {"ok": True, "out": str(p), "count": 1}

    def _prepare_pack(src_path: str, out_dir: str, format: str, train_ratio: float, seed: int, min_output_chars: int, dedupe_by_instruction: bool) -> Dict[str, Any]:  # noqa: ANN001
        # Create dummy train/val outputs
        out = Path(out_dir)
        (out / "train.jsonl").write_text("{}\n", encoding="utf-8")
        (out / "val.jsonl").write_text("{}\n", encoding="utf-8")
        return {"ok": True, "train": str(out / "train.jsonl"), "val": str(out / "val.jsonl"), "counts": {"train":1,"val":1}}

    # Patch the imported modules inside script
    monkeypatch.setattr(mod, "_export", types.SimpleNamespace(export_from_results=_export))
    monkeypatch.setattr(mod, "_prepare", types.SimpleNamespace(prepare_pack=_prepare_pack))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        # Simuliere CLI-Aufruf
        mod.sys.argv = ["curate_dataset_from_latest.py", "--results-dir", str(res_dir), "--format", "openai_chat" ]
        rc = mod.main()
    assert rc == 0
    out = buf.getvalue()
    assert "\"ok\": true" in out.lower()
    assert "train" in out and "val" in out
