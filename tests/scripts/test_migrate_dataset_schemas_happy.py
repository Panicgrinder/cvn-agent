from __future__ import annotations

import importlib
from pathlib import Path
import json
import io
import contextlib
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_migrate_demo_dataset_happy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.migrate_dataset_schemas")

    # Baue Projektstruktur im tmp nach: eval/datasets/eval-21-40_fantasy_v1.0.json
    proj = tmp_path / "proj"
    datasets = proj / "eval" / "datasets"
    datasets.mkdir(parents=True)
    src = datasets / "eval-21-40_fantasy_v1.0.json"
    # Mische JSON-Array mit prompt und must_include
    entries: list[dict[str, object]] = [
        {"id": "eval-1", "prompt": "Hi", "must_include": ["x"]},
        {"id": "eval-2", "messages": [{"role":"user","content":"Hey"}], "must_include": ["y"]},
    ]
    src.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")

    # CWD auf Projektwurzel setzen
    monkeypatch.chdir(str(proj))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ok = mod.migrate_demo_dataset()
    assert ok is True
    out = buf.getvalue()
    assert "Gefunden: 2 Einträge" in out
    assert "prompt -> messages migriert" in out
    assert "must_include" in out  # irgendeine Migration dieses Feldes

    # Ergebnisdatei wurde in JSONL geschrieben
    lines = src.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    rec1 = json.loads(lines[0])
    assert "messages" in rec1 and "prompt" not in rec1
    assert "checks" in rec1 and "must_include" not in rec1
    # Backup existiert
    assert (src.with_suffix(src.suffix + ".backup")).exists()
