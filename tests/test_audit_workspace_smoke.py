from __future__ import annotations

import os
import io
from contextlib import redirect_stdout

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_audit_workspace_runs_and_prints(tmp_path: "os.PathLike[str]") -> None:
    # Wir lenken die Projektwurzel temporär auf ein Mini-Workspace um
    # und erzeugen eine kleine Struktur mit 1 Python-Datei und 1 Markdown.
    ws = tmp_path
    for p in ["app", "scripts", "utils", "docs", "eval", "examples"]:
        os.makedirs(os.path.join(ws, p), exist_ok=True)
    pyfile = os.path.join(ws, "app", "mini.py")
    with open(pyfile, "w", encoding="utf-8") as f:
        f.write("def x():\n    return 1\n")
    mdfile = os.path.join(ws, "docs", "readme.md")
    with open(mdfile, "w", encoding="utf-8") as f:
        f.write("# Titel\nText\n")

    from scripts import audit_workspace as aw
    aw.PROJECT_ROOT = str(ws)

    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = aw.main()
    out = buf.getvalue()
    assert rc == 0
    # Prüfe, dass Kopf/Struktur des Reports vorhanden ist
    assert "= Audit Bericht =" in out
    assert "Projektwurzel:" in out
