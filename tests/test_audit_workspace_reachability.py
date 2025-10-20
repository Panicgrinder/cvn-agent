from __future__ import annotations

import os
import io
from contextlib import redirect_stdout

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_audit_reachability_graph(tmp_path: "os.PathLike[str]") -> None:
    # Mini-Workspace: app.mod1 imports utils.mod2
    ws = tmp_path
    os.makedirs(os.path.join(ws, "app"), exist_ok=True)
    os.makedirs(os.path.join(ws, "utils"), exist_ok=True)
    with open(os.path.join(ws, "app", "mod1.py"), "w", encoding="utf-8") as f:
        f.write("import utils.mod2\n\nCONST=1\n")
    with open(os.path.join(ws, "utils", "mod2.py"), "w", encoding="utf-8") as f:
        f.write("VALUE=2\n")

    from scripts import audit_workspace as aw
    aw.PROJECT_ROOT = str(ws)

    pyfiles = aw.discover_pyfiles()
    graph = aw.build_graph(pyfiles)
    entry_mods = ["app.mod1"]
    reachable = aw.reachable_from(entry_mods, graph)
    assert "app.mod1" in reachable
    assert "utils.mod2" in reachable

    # Full main() run prints counts; ensure it executes without error and prints header
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = aw.main()
    out = buf.getvalue()
    assert rc == 0
    assert "= Audit Bericht =" in out
