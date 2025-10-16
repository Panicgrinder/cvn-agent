from __future__ import annotations

import os
import io
from contextlib import redirect_stdout
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_map_reduce_summary_generates_outputs(monkeypatch: "pytest.MonkeyPatch", tmp_path: "os.PathLike[str]") -> None:
    # Erzeuge minimalen Scope mit 2 Dateien
    scope_dir = os.path.join(tmp_path, "myscope")
    os.makedirs(scope_dir, exist_ok=True)
    p1 = os.path.join(scope_dir, "a.py")
    with open(p1, "w", encoding="utf-8") as f:
        f.write("def a():\n    pass\n")
    p2 = os.path.join(scope_dir, "b.md")
    with open(p2, "w", encoding="utf-8") as f:
        f.write("# H1\n- item\n")

    out_dir = os.path.join(tmp_path, "out")
    from scripts import map_reduce_summary as m
    # Patch SCOPES auf einen temporären Eintrag
    m.SCOPES = {"myscope": scope_dir}
    # Führe main mit begrenzter Dateizahl pro Scope aus
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = m.main(["--scopes", "myscope", "--max-files", "2", "--out-dir", out_dir])
    out = buf.getvalue()
    assert rc == 0
    # Es sollte eine JSON-Zusammenfassung ausgegeben worden sein
    assert "\"files\"" in out and out.strip().endswith("}")
    # Und Dateien erzeugt worden sein
    assert os.path.isdir(out_dir)
    assert any(name.startswith("summary_") for name in os.listdir(out_dir))
