from __future__ import annotations

import os
import io
from contextlib import redirect_stdout
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_fine_tune_pipeline_minimal_flows(tmp_path: "os.PathLike[str]") -> None:
    out_dir = os.path.join(tmp_path, "eval", "results", "finetune")
    os.makedirs(out_dir, exist_ok=True)

    from scripts import fine_tune_pipeline as ftp
    # Patch argv: kein train file vorhanden -> sollte mit Code 2 enden
    import sys
    old_argv = sys.argv[:]
    sys.argv = ["fine_tune_pipeline.py", "--finetune-dir", out_dir]
    try:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ftp.main()
        assert rc == 2
        assert "Keine Train-Datei gefunden" in buf.getvalue()
    finally:
        sys.argv = old_argv

    # Jetzt simuliere eine vorhandene Train-Datei, aber blocke nicht erlaubtes Modell
    train_fp = os.path.join(out_dir, "finetune_demo_train.jsonl")
    with open(train_fp, "w", encoding="utf-8") as f:
        f.write("{}\n")

    old_argv = sys.argv[:]
    sys.argv = [
        "fine_tune_pipeline.py",
        "--finetune-dir", out_dir,
        "--model", "some/private-model",
        "--no-check",
    ]
    try:
        buf2 = io.StringIO()
        with redirect_stdout(buf2):
            rc2 = ftp.main()
        assert rc2 == 4
        assert "nicht in der Free-Allowlist" in buf2.getvalue()
    finally:
        sys.argv = old_argv
