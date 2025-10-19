from __future__ import annotations

import importlib
import io
import json
import contextlib
from pathlib import Path
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_summarize_python_ast(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.map_reduce_summary")

    root = tmp_path / "pys"
    root.mkdir()
    py = root / "x.py"
    py.write_text(
        (
            '"""Modul-Doc"""\n\n'
            "class A:\n"
            "    def m1(self):\n"
            "        pass\n\n"
            "def f1():\n"
            "    pass\n\n"
            "CONST = 1\n"
        ),
        encoding="utf-8",
    )

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    monkeypatch.setitem(mod.SCOPES, "PYS", str(root))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main(["--scopes", "PYS", "--out-dir", str(out_dir), "--max-files", "5"])
    assert rc == 0
    data = json.loads(buf.getvalue())
    merged = Path(data["merged"]).read_text(encoding="utf-8")
    assert "Klassen:" in merged
    assert "Funktionen:" in merged
    assert "Konstanten:" in merged


@pytest.mark.scripts
@pytest.mark.unit
def test_summarize_json_and_jsonl(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.map_reduce_summary")

    root = tmp_path / "jsons"
    root.mkdir()
    j1 = root / "arr.json"
    j1.write_text(json.dumps([{"a": 1, "b": 2}, {"a": 2, "c": 3}]), encoding="utf-8")

    j2 = root / "lines.jsonl"
    j2.write_text("\n".join([json.dumps({"x": i, "y": i * 2}) for i in range(5)]), encoding="utf-8")

    out_dir = tmp_path / "out2"
    out_dir.mkdir()
    monkeypatch.setitem(mod.SCOPES, "JSONS", str(root))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = mod.main(["--scopes", "JSONS", "--out-dir", str(out_dir), "--max-files", "10"])
    assert rc == 0
    data = json.loads(buf.getvalue())
    merged = Path(data["merged"]).read_text(encoding="utf-8")
    assert "JSON-Array" in merged or "JSONL" in merged
