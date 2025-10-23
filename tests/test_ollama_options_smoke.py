from __future__ import annotations

from typing import Any, Dict

from app.api.chat_helpers import normalize_ollama_options


def test_normalize_ollama_options_extended_fields() -> None:
    raw: Dict[str, Any] = {
        "temperature": 0.9,
        "max_tokens": 128,
        "num_ctx": 2048,
        "repeat_penalty": 1.1,
        "presence_penalty": 0.2,
        "frequency_penalty": 0.3,
        "seed": 42,
        "repeat_last_n": 64,
        "stop": ["\n\n", "<END>"]
    }
    opts, host = normalize_ollama_options(raw, eval_mode=False)
    assert isinstance(opts, dict) and isinstance(host, str)
    assert opts["num_predict"] == 128
    assert opts["temperature"] == 0.9
    assert opts["num_ctx"] == 2048
    assert opts["repeat_penalty"] == 1.1
    assert opts["presence_penalty"] == 0.2
    assert opts["frequency_penalty"] == 0.3
    assert opts["seed"] == 42
    assert opts["repeat_last_n"] == 64
    assert opts["stop"] == ["\n\n", "<END>"]


def test_eval_mode_caps_temperature() -> None:
    raw: Dict[str, Any] = {"temperature": 0.8, "max_tokens": 5}
    opts, _ = normalize_ollama_options(raw, eval_mode=True)
    assert opts["temperature"] <= 0.25
    assert opts["num_predict"] == 5
