import types
import importlib.abc
import pytest
import scripts.quick_eval as qe
from importlib.machinery import ModuleSpec


@pytest.mark.scripts
@pytest.mark.unit
def test_load_run_eval_module_minimal(monkeypatch):
    # Provide a tiny fake run_eval module via spec loader path
    class Loader(importlib.abc.Loader):
        def create_module(self, spec: ModuleSpec):
            return types.ModuleType("run_eval")
        def exec_module(self, module):
            from typing import Any, cast
            m = cast(Any, module)
            # inject the attributes accessed in quick_eval
            m.DEFAULT_DATASET_DIR = "eval/datasets"
            m.DEFAULT_RESULTS_DIR = "eval/results"
            m.DEFAULT_FILE_PATTERN = "eval-*.jsonl"
            m.run_evaluation = lambda **kwargs: []  # no-op returning empty list
            m.print_results = lambda results: None

    def fake_spec_from_file_location(name: str, path: str):
        return ModuleSpec(name=name, loader=Loader())

    # pyright: ignore[reportUnknownMemberType] - dynamic patch for test hook
    monkeypatch.setattr("importlib.util.spec_from_file_location", fake_spec_from_file_location)  # type: ignore[attr-defined]

    mod = qe._load_run_eval_module()
    assert hasattr(mod, "run_evaluation")
    assert hasattr(mod, "print_results")