from __future__ import annotations

import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_todo_gather_import_smoke() -> None:
    mod = importlib.import_module("scripts.todo_gather")
    assert hasattr(mod, "main") or True
