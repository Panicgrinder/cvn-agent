from __future__ import annotations

import importlib
import types
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_quick_eval_main_with_stub(monkeypatch: pytest.MonkeyPatch) -> None:
    mod = importlib.import_module("scripts.quick_eval")

    # Stub _load_run_eval_module to return a fake module with expected attributes
    fake = types.SimpleNamespace()
    fake.DEFAULT_DATASET_DIR = ".tmp-datasets"
    fake.DEFAULT_RESULTS_DIR = ".tmp-results"
    fake.DEFAULT_FILE_PATTERN = "eval-*.jsonl"

    from typing import Any, List
    async def _run_evaluation(**kwargs: Any) -> List[Any]:
        return []

    def _print_results(results: object) -> None:
        pass

    fake.run_evaluation = _run_evaluation
    fake.print_results = _print_results

    monkeypatch.setattr(mod, "_load_run_eval_module", lambda: fake)

    rc = mod.main()
    assert rc == 0
