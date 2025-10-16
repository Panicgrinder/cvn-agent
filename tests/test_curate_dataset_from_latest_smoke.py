from __future__ import annotations

import io
import json
import os
from types import SimpleNamespace
from typing import Any, Dict
from pathlib import Path

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_curate_dataset_from_latest_smoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange temp results dir with a dummy results file and minimal content
    results_dir: Path = tmp_path / "eval" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    results_file = results_dir / "results_20250101_0000.jsonl"
    # one successful row, one failed
    results_file.write_text(
        "\n".join([
            json.dumps({
                "item_id": "eval-abc123",
                "success": True,
                "response": "Antworttext mit ausreichender Länge für den Filter.",
                "failed_checks": []
            }),
            json.dumps({
                "item_id": "missing-id",
                "success": False,
                "response": "",
                "failed_checks": ["noop"]
            })
        ]),
        encoding="utf-8"
    )

    # Stub export_from_results to return a tiny exported file we control
    exported: Path = results_dir / "finetune" / "finetune_openai_chat_results_20250101_0000_20250101_0101.jsonl"
    exported.parent.mkdir(parents=True, exist_ok=True)
    exported.write_text(
        "\n".join([
            json.dumps({
                "messages": [
                    {"role": "system", "content": "sys"},
                    {"role": "user", "content": "instr"},
                    {"role": "assistant", "content": "kurze antwort"}
                ],
                "meta": {"id": "eval-abc123", "package": "pkg", "success": True, "failed_checks": []}
            }),
            json.dumps({
                "messages": [
                    {"role": "user", "content": "instr 2"},
                    {"role": "assistant", "content": "noch eine antwort mit ausreichender länge"}
                ],
                "meta": {"id": "eval-abc124", "package": "pkg", "success": True, "failed_checks": []}
            })
        ]),
        encoding="utf-8"
    )

    async def fake_export(results_path: str, out_dir: str | None = None, format: str = "openai_chat", include_failures: bool = False, patterns: list[str] | None = None) -> Dict[str, Any]:  # type: ignore[override]
        return {"ok": True, "out": str(exported), "count": 2}

    def fake_prepare(src_path: str, out_dir: str | None = None, format: str = "openai_chat", train_ratio: float = 0.9, seed: int = 42, min_output_chars: int = 20, dedupe_by_instruction: bool = True) -> Dict[str, Any]:  # type: ignore[override]
        # create minimal train/val based on src_path
        assert os.path.exists(src_path)
        out_dir2 = out_dir or os.path.dirname(src_path)
        base = os.path.splitext(os.path.basename(src_path))[0]
        train = os.path.join(out_dir2, f"{base}_train.jsonl")
        val = os.path.join(out_dir2, f"{base}_val.jsonl")
        with open(train, "w", encoding="utf-8") as f:
            f.write("{}\n")
        with open(val, "w", encoding="utf-8") as f:
            f.write("{}\n")
        return {"ok": True, "train": train, "val": val, "counts": {"train": 1, "val": 1, "total": 2}}

    # Isoliere argparse von pytest-Args und setze --results-dir auf tmp
    import sys
    monkeypatch.setattr(sys, "argv", [
        "curate_dataset_from_latest.py",
        "--results-dir",
        str(results_dir),
    ])

    import importlib
    mod = importlib.import_module("scripts.curate_dataset_from_latest")

    # Monkeypatch export and prepare
    monkeypatch.setattr(mod, "_export", SimpleNamespace(export_from_results=fake_export))
    monkeypatch.setattr(mod, "_prepare", SimpleNamespace(prepare_pack=fake_prepare))

    # Capture stdout
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = mod.main()

    assert rc == 0
    out = buf.getvalue()
    payload = json.loads(out)
    assert payload.get("ok") is True
    assert os.path.dirname(str(payload["export"])) == os.path.join(str(results_dir), "finetune")
    assert "train" in payload and "val" in payload
