from __future__ import annotations

import importlib
from pathlib import Path
import io
import contextlib
import types
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_pipeline_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.fine_tune_pipeline")

    # train file
    train = tmp_path / "finetune_foo_train.jsonl"
    train.write_text("{}\n", encoding="utf-8")
    def _latest_train_file(*_a: object, **_k: object) -> str:
        return str(train)
    monkeypatch.setattr(mod, "latest_train_file", _latest_train_file)
    monkeypatch.setattr(mod, "env_check", lambda: None)

    # subprocess.call raises KeyboardInterrupt
    def _call(args: list[str] | tuple[str, ...]):  # noqa: ANN001
        raise KeyboardInterrupt()
    monkeypatch.setattr(mod, "subprocess", types.SimpleNamespace(call=_call))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        monkeypatch.setattr(mod.sys, "argv", [
            "fine_tune_pipeline.py", "--model", "gpt2", "--epochs", "1", "--no-check"
        ])
        rc = mod.main()
    assert rc == 130


@pytest.mark.scripts
@pytest.mark.unit
def test_pipeline_fp16_flag(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    mod = importlib.import_module("scripts.fine_tune_pipeline")
    train = tmp_path / "finetune_foo_train.jsonl"
    train.write_text("{}\n", encoding="utf-8")
    def _latest_train_file2(*_a: object, **_k: object) -> str:
        return str(train)
    monkeypatch.setattr(mod, "latest_train_file", _latest_train_file2)
    monkeypatch.setattr(mod, "env_check", lambda: None)

    calls: list[list[str]] = []
    def _call(args: list[str] | tuple[str, ...]):  # noqa: ANN001
        calls.append(list(args))
        return 0
    monkeypatch.setattr(mod, "subprocess", types.SimpleNamespace(call=_call))

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        monkeypatch.setattr(mod.sys, "argv", [
            "fine_tune_pipeline.py", "--model", "gpt2", "--epochs", "1", "--fp16", "--no-check"
        ])
        rc = mod.main()
    assert rc == 0
    # ensure --fp16 flag is passed through
    assert any("--fp16" in part for call in calls for part in call)
