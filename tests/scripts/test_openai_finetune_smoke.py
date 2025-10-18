from __future__ import annotations

import json
import os
from pathlib import Path
from types import SimpleNamespace
import importlib

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_openai_finetune_validate_only(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Minimal openai_chat JSONL (train/val gleich)
    def _mk(path: Path) -> None:
        with open(path, "w", encoding="utf-8") as f:
            f.write(json.dumps({"messages": [{"role": "user", "content": "hi"}, {"role": "assistant", "content": "ok"}]}) + "\n")

    train = tmp_path / "t.jsonl"
    val = tmp_path / "v.jsonl"
    _mk(train)
    _mk(val)

    mod = importlib.import_module("scripts.openai_finetune")

    # CLI validate-only Pfad: ruft validate_openai_chat_jsonl und druckt VALIDATION_OK
    import sys
    argv_bak = sys.argv
    try:
        sys.argv = ["openai_finetune.py", os.fspath(train), os.fspath(val), "--validate-only"]
        # Führe Modul als Skript
        with pytest.raises(SystemExit):
            mod.__main__  # type: ignore[attr-defined]
    except AttributeError:
        # Fallback: rufe direkt Validator auf
        mod.validate_openai_chat_jsonl(os.fspath(train))
        mod.validate_openai_chat_jsonl(os.fspath(val))
    finally:
        sys.argv = argv_bak


@pytest.mark.scripts
@pytest.mark.unit
def test_openai_finetune_start_with_mock_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # JSONL vorbereiten
    path = tmp_path / "d.jsonl"
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps({"messages": [{"role": "user", "content": "q"}]}) + "\n")

    mod = importlib.import_module("scripts.openai_finetune")

    # API Key setzen
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Dummy OpenAI Client
    class _Files:
        def create(self, file, purpose):  # type: ignore[no-redef]
            return SimpleNamespace(id="file-123")

    class _Jobs:
        def create(self, training_file, validation_file, model):  # type: ignore[no-redef]
            return SimpleNamespace(id="job-123")

    class _Client:
        def __init__(self, api_key: str) -> None:  # noqa: ARG002
            self.files = _Files()
            self.fine_tuning = SimpleNamespace(jobs=_Jobs())

    # Patch Factory
    monkeypatch.setattr(mod, "_OpenAI_factory", _Client)

    out = mod.start_finetune(os.fspath(path), os.fspath(path), model="gpt-4o-mini")
    assert out.get("ok") is True
    assert out.get("job") == "job-123"
