import pytest
from typing import Any, Dict

from app.api.chat_helpers import normalize_ollama_options
from app.core.settings import settings


@pytest.mark.unit
def test_normalize_includes_defaults_when_missing() -> None:
    opts, host = normalize_ollama_options({}, eval_mode=False)
    # Basisfelder vorhanden
    assert isinstance(opts["temperature"], float)
    assert isinstance(opts["num_predict"], int)
    # Sampling-Defaults aus Settings sollten übernommen werden
    assert pytest.approx(opts.get("top_p"), rel=0, abs=1e-9) == settings.TOP_P
    assert opts.get("top_k") == settings.TOP_K
    # Host aus Settings
    assert host == settings.OLLAMA_HOST


@pytest.mark.unit
def test_stop_string_is_coerced_to_list() -> None:
    raw: Dict[str, Any] = {"stop": "END"}
    opts, _ = normalize_ollama_options(raw, eval_mode=False)
    assert opts.get("stop") == ["END"]


@pytest.mark.unit
def test_mirostat_and_clamping() -> None:
    raw: Dict[str, Any] = {
        "mirostat": 5,              # wird auf 2 geklemmt
        "min_p": 1.5,               # auf 1.0 geklemmt
        "typical_p": -0.2,          # auf 0.0 geklemmt
        "tfs_z": 2,                 # auf 1.0 geklemmt
        "penalize_newline": "true"
    }
    opts, _ = normalize_ollama_options(raw, eval_mode=False)
    assert opts.get("mirostat") == 2
    assert 0.0 <= float(opts.get("min_p", 0.0)) <= 1.0
    assert 0.0 <= float(opts.get("typical_p", 0.0)) <= 1.0
    assert 0.0 <= float(opts.get("tfs_z", 0.0)) <= 1.0
    assert opts.get("penalize_newline") is True


@pytest.mark.unit
def test_eval_mode_caps_temperature() -> None:
    raw: Dict[str, Any] = {"temperature": 0.9}
    opts, _ = normalize_ollama_options(raw, eval_mode=True)
    assert opts["temperature"] <= 0.25
