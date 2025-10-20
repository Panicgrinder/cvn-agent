from __future__ import annotations

import os
from pathlib import Path
import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_migrate_dataset_schemas_empty_and_missing(tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.migrate_dataset_schemas")
    proj = tmp_path
    eval_dir = proj / "eval" / "datasets"
    eval_dir.mkdir(parents=True, exist_ok=True)
    # Erzeuge leere Datei am Default-Pfad
    target = eval_dir / "eval-21-40_fantasy_v1.0.json"
    target.write_text("\n", encoding="utf-8")

    cwd_before = os.getcwd()
    os.chdir(os.fspath(proj))
    try:
        ok_empty = mod.migrate_demo_dataset()
        assert ok_empty is False

        # Lösche Datei komplett → fehlend
        target.unlink()
        ok_missing = mod.migrate_demo_dataset()
        assert ok_missing is False
    finally:
        os.chdir(cwd_before)


@pytest.mark.scripts
@pytest.mark.unit
def test_migrate_dataset_schemas_jsonl_no_entries(tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.migrate_dataset_schemas")
    proj = tmp_path
    eval_dir = proj / "eval" / "datasets"
    eval_dir.mkdir(parents=True, exist_ok=True)
    target = eval_dir / "eval-21-40_fantasy_v1.0.json"
    # Schreibe JSONL mit nur Leerzeilen
    target.write_text("\n\n\n", encoding="utf-8")

    cwd_before = os.getcwd()
    os.chdir(os.fspath(proj))
    try:
        ok = mod.migrate_demo_dataset()
        assert ok is False
    finally:
        os.chdir(cwd_before)
