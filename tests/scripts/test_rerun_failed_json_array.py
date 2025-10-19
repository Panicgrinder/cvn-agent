from __future__ import annotations

import importlib
import io
import json
import contextlib
from pathlib import Path
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_rerun_failed_with_json_array(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.rerun_failed")

    # Prepare fake results with one failed id
    results_dir = tmp_path / "eval" / "results"
    results_dir.mkdir(parents=True)
    results_file = results_dir / "results_20250101_0000.jsonl"
    # include a success and a failure
    rows: list[dict[str, object]] = [
        {"id": "eval-1", "success": True},
        {"id": "eval-2", "success": False},
    ]
    results_file.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")

    # Prepare datasets as JSON array (not JSONL)
    datasets_dir = tmp_path / "eval" / "datasets"
    datasets_dir.mkdir(parents=True)
    arr_path = datasets_dir / "eval-sample.json"
    arr_path.write_text(json.dumps([
        {"id": "eval-2", "messages": [{"role": "user", "content": "hi"}]},
        {"id": "eval-3", "messages": [{"role": "user", "content": "x"}]},
    ]), encoding="utf-8")

    tmp_dir = results_dir / "tmp"
    monkeypatch.setattr(mod, "RESULTS_DIR", str(results_dir))
    monkeypatch.setattr(mod, "DATASETS_DIR", str(datasets_dir))
    monkeypatch.setattr(mod, "TMP_DIR", str(tmp_dir))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main()
    assert rc == 0
    out = buf.getvalue()
    assert "Re-Run Dataset erstellt" in out
    # ensure file exists and contains the failed item
    created = list(tmp_dir.glob("rerun_*.jsonl"))
    assert created, "Expected a rerun file to be created"
    content = created[0].read_text(encoding="utf-8")
    assert "eval-2" in content
