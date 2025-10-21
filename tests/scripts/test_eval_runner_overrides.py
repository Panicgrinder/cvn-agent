from __future__ import annotations

import importlib


def test_resolve_profile_overrides_defaults_eval_profile() -> None:
    run_eval = importlib.import_module("scripts.run_eval")
    t, p, n, eval_mode = run_eval.resolve_profile_overrides("eval", None, None, None)
    assert eval_mode is True
    assert t == 0.2
    assert p == 0.1
    assert n == 128


def test_resolve_profile_overrides_preserve_manual_values() -> None:
    run_eval = importlib.import_module("scripts.run_eval")
    # Manuelle Werte dürfen nicht überschrieben werden
    t, p, n, eval_mode = run_eval.resolve_profile_overrides("eval", 0.05, 0.7, 64)
    assert eval_mode is True
    assert t == 0.05
    assert p == 0.7
    assert n == 64


def test_normalize_checks_alias_and_commas() -> None:
    run_eval = importlib.import_module("scripts.run_eval")
    checks = run_eval.normalize_checks(["rpg_style, term_inclusion", "regex"])  # mixed
    # term_inclusion -> must_include, keywords_any, keywords_at_least
    assert checks is not None
    assert "rpg_style" in checks
    assert "regex" in checks
    for c in ("must_include", "keywords_any", "keywords_at_least"):
        assert c in checks
