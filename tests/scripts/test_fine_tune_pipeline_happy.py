from __future__ import annotations

import importlib
from pathlib import Path
import io
import contextlib
import types
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_pipeline_happy_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.fine_tune_pipeline")

    # Stub latest_train_file to return a fake path
    fake_train = tmp_path / "train.jsonl"
    fake_train.write_text("{}\n", encoding="utf-8")
    def _latest_train_file(*_args: object, **_kw: object) -> str:
        return str(fake_train)
    monkeypatch.setattr(mod, "latest_train_file", _latest_train_file)

    # Stub env_check to pass
    def _env_check(*_args: object, **_kw: object) -> None:
        return None
    monkeypatch.setattr(mod, "env_check", _env_check)

    calls: list[list[str]] = []

    def _run(args: list[str] | tuple[str, ...], check: bool = False):  # noqa: ANN001
        # capture args and emulate success
        arg_list = list(args)
        calls.append(arg_list)
        return 0

    monkeypatch.setattr(mod, "subprocess", types.SimpleNamespace(call=_run))

    # Execute main with required args
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        # Simuliere CLI-Aufruf
        monkeypatch.setattr(mod.sys, "argv", ["fine_tune_pipeline.py", "--model", "gpt2", "--epochs", "1", "--bf16", "--no-check"])  # noqa: E501
        rc = mod.main()  # bf16 branch

    assert rc == 0
    assert any("gpt2" in " ".join(c) for c in calls)
    # Ensure train file used
    assert any(str(fake_train) in " ".join(c) for c in calls)
