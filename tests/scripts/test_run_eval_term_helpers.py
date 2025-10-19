from __future__ import annotations

from typing import List

import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_get_term_variants_basic() -> None:
    import importlib
    run_eval = importlib.import_module("scripts.run_eval")
    variants: List[str] = run_eval.get_term_variants("Planung")
    vset = {v.lower() for v in variants}
    # Erwartet: Grundform, Stamm, -en Form, Pluralvarianten
    # Die Implementierung liefert die ursprüngliche Schreibweise, nicht zwingend lowercased
    assert "planung" in vset
    assert "plan" in vset  # "Planung" -> "plan"
    assert "planen" in vset  # "Planung" -> "planen"
    assert ("planung" + "en") in vset  # generische Pluralableitung


@pytest.mark.scripts
@pytest.mark.unit
def test_check_term_inclusion_with_variants_and_synonyms(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib
    run_eval = importlib.import_module("scripts.run_eval")

    # Synonyme deterministisch machen
    def _fake_synonyms(term: str) -> List[str]:
        # Für "sicherheit" und "risiko" künstliche Synonyme liefern
        if term in ("sicherheit", "sicher"):
            return ["schutz", "absicherung"]
        if term in ("risiko",):
            return ["gefahr"]
        return []

    monkeypatch.setattr(run_eval, "get_synonyms", _fake_synonyms, raising=True)

    text = (
        "Wir planen Maßnahmen zur Absicherung. "
        "Die Gefahr wird minimiert und ein sicherer Betrieb gewährleistet."
    ).lower()

    # Direkte Enthaltenheit
    assert run_eval.check_term_inclusion(text, "gefahr") is True
    # Über Synonyme (risiko -> gefahr)
    assert run_eval.check_term_inclusion(text, "risiko") is True
    # Varianten (Sicherheit -> sicher)
    assert run_eval.check_term_inclusion(text, "Sicherheit") is True
    # Zusammengesetzter Begriff: beide Wörter (oder Synonyme) im Text
    assert run_eval.check_term_inclusion(text, "sichere gefahr") is True
