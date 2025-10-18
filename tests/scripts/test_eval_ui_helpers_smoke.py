from __future__ import annotations

import importlib
import os
from pathlib import Path

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_eval_ui_list_and_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ui = importlib.import_module("scripts.eval_ui")

    # Umleiten der Verzeichnisse von run_eval-Defaults auf tmp
    # eval/config und eval/datasets unter tmp
    config_dir = tmp_path / "eval" / "config"
    datasets_dir = tmp_path / "eval" / "datasets"
    results_dir = tmp_path / "eval" / "results"
    config_dir.mkdir(parents=True, exist_ok=True)
    datasets_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    # monkeypatch run_eval module attributes used by eval_ui
    run_eval = ui.run_eval
    monkeypatch.setattr(run_eval, "DEFAULT_EVAL_DIR", os.fspath(datasets_dir), raising=False)
    monkeypatch.setattr(run_eval, "DEFAULT_DATASET_DIR", os.fspath(datasets_dir), raising=False)
    monkeypatch.setattr(run_eval, "DEFAULT_CONFIG_DIR", os.fspath(config_dir), raising=False)
    monkeypatch.setattr(run_eval, "DEFAULT_RESULTS_DIR", os.fspath(results_dir), raising=False)

    # Stelle sicher, dass ensure_eval_files_exist eine Demo-Datei erzeugt
    ui.ensure_eval_files_exist()
    pkgs = ui.list_eval_packages()
    assert isinstance(pkgs, list)
    assert pkgs, "Demo-Eval-Datei sollte angelegt worden sein"

    # Profile speichern/lesen Roundtrip
    prof_path = ui.profiles_path()
    assert prof_path.endswith("profiles.json")
    data = ui.load_profiles()
    data["default"]["quiet"] = True
    ui.save_profiles(data)
    data2 = ui.load_profiles()
    assert data2.get("default", {}).get("quiet") is True
