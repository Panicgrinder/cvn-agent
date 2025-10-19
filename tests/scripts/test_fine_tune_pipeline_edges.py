from __future__ import annotations

import os
import io
import json
import importlib
import contextlib
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_pipeline_no_train_file_returns_2(tmp_path: "os.PathLike[str]") -> None:
    mod = importlib.import_module("scripts.fine_tune_pipeline")
    # leerer finetune-dir
    fin_dir = os.path.join(tmp_path, "finetune")
    os.makedirs(fin_dir, exist_ok=True)
    import sys
    argv_bak = sys.argv[:]
    try:
        sys.argv = ["fine_tune_pipeline.py", "--finetune-dir", fin_dir]
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = mod.main()
        assert rc == 2
    finally:
        sys.argv = argv_bak


@pytest.mark.scripts
@pytest.mark.unit
def test_pipeline_model_guard_denies_non_free(tmp_path: "os.PathLike[str]") -> None:
    mod = importlib.import_module("scripts.fine_tune_pipeline")
    # Fake train-file
    fin_dir = os.path.join(tmp_path, "finetune")
    os.makedirs(fin_dir, exist_ok=True)
    train = os.path.join(fin_dir, "finetune_foo_train.jsonl")
    with open(train, "w", encoding="utf-8") as f:
        f.write("{}\n")
    import sys
    argv_bak = sys.argv[:]
    try:
        sys.argv = [
            "fine_tune_pipeline.py",
            "--finetune-dir", fin_dir,
            "--train-file", train,
            "--model", "not/free",
        ]
        rc = mod.main()
        assert rc == 4
    finally:
        sys.argv = argv_bak


@pytest.mark.scripts
@pytest.mark.unit
def test_pipeline_env_check_blocks_missing_packages(monkeypatch: pytest.MonkeyPatch, tmp_path: "os.PathLike[str]") -> None:
    mod = importlib.import_module("scripts.fine_tune_pipeline")
    fin_dir = os.path.join(tmp_path, "finetune")
    os.makedirs(fin_dir, exist_ok=True)
    train = os.path.join(fin_dir, "finetune_foo_train.jsonl")
    with open(train, "w", encoding="utf-8") as f:
        f.write("{}\n")
    # env_check soll hartes Problem melden
    monkeypatch.setattr(mod, "env_check", lambda: "torch nicht importierbar; bitte PyTorch installieren.")
    import sys
    argv_bak = sys.argv[:]
    try:
        sys.argv = [
            "fine_tune_pipeline.py",
            "--finetune-dir", fin_dir,
            "--train-file", train,
            "--model", mod.FREE_MODEL_ALLOWLIST[0],
        ]
        rc = mod.main()
        assert rc == 3
    finally:
        sys.argv = argv_bak
