from __future__ import annotations

import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_run_eval_imports_smoke() -> None:
    mod = importlib.import_module("scripts.run_eval")
    # Ein paar Kern-Attribute vorhanden?
    for attr in [
        "DEFAULT_EVAL_DIR",
        "DEFAULT_DATASET_DIR",
        "DEFAULT_RESULTS_DIR",
        "DEFAULT_CONFIG_DIR",
        "DEFAULT_FILE_PATTERN",
    ]:
        assert hasattr(mod, attr)
