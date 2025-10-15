import types
import importlib.abc
import scripts.quick_eval as qe
from importlib.machinery import ModuleSpec


def test_load_run_eval_module_minimal(monkeypatch):
    # Provide a tiny fake run_eval module via spec loader path
    class Loader(importlib.abc.Loader):
        def create_module(self, spec):
            return types.ModuleType("run_eval")
        def exec_module(self, module):
            # inject the attributes accessed in quick_eval
            module.DEFAULT_DATASET_DIR = "eval/datasets"
            module.DEFAULT_RESULTS_DIR = "eval/results"
            module.DEFAULT_FILE_PATTERN = "eval-*.jsonl"
            module.run_evaluation = lambda **kwargs: []  # no-op returning empty list
            module.print_results = lambda results: None

    def fake_spec_from_file_location(name, path):
        return ModuleSpec(name=name, loader=Loader())

    monkeypatch.setattr("importlib.util.spec_from_file_location", fake_spec_from_file_location)

    mod = qe._load_run_eval_module()
    assert hasattr(mod, "run_evaluation")
    assert hasattr(mod, "print_results")