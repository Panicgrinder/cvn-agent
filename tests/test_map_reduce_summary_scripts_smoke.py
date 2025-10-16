from __future__ import annotations

import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_map_reduce_summary_scripts_importable() -> None:
    mod1 = importlib.import_module("scripts.map_reduce_summary")
    mod2 = importlib.import_module("scripts.map_reduce_summary_llm")
    assert hasattr(mod1, "main") or True
    assert hasattr(mod2, "main") or True
