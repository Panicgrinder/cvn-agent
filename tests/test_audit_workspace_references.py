from __future__ import annotations

import os
import io
from contextlib import redirect_stdout

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_audit_workspace_scan_text_references_positive(tmp_path: "os.PathLike[str]") -> None:
    # Mini-Workspace aufbauen
    ws = tmp_path
    for p in ["app", "docs"]:
        os.makedirs(os.path.join(ws, p), exist_ok=True)
    # Datei, auf die verwiesen wird
    mdfile = os.path.join(ws, "docs", "ref_notes.md")
    with open(mdfile, "w", encoding="utf-8") as f:
        f.write("# Notizen\n")
    # Python-Datei, die den Dateinamen erwähnt
    pyfile = os.path.join(ws, "app", "uses_ref.py")
    with open(pyfile, "w", encoding="utf-8") as f:
        f.write("# siehe ref_notes.md für Details\n")

    from scripts import audit_workspace as aw
    aw.PROJECT_ROOT = str(ws)

    refs = aw.scan_text_references()
    # Prüfen über Basename, um Pfadunterschiede (Drives) zu abstrahieren
    assert any(os.path.basename(p) == "ref_notes.md" for p in refs)

    # optional: kompletter Lauf druckt Referenzen mit aus
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = aw.main()
    out = buf.getvalue()
    assert rc == 0
    assert "Nicht-Python-Dateien mit Referenzen im Code:" in out
    assert "ref_notes.md" in out
