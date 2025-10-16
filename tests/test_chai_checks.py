from typing import Dict, Any, List

# Wir importieren check_term_inclusion aus run_eval, um die gleiche Logik wie im Evaluator zu verwenden
import importlib.util
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN_EVAL_PATH = os.path.join(PROJECT_ROOT, "scripts", "run_eval.py")
spec = importlib.util.spec_from_file_location("run_eval", RUN_EVAL_PATH)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)  # type: ignore
check_term_inclusion = getattr(module, "check_term_inclusion")


def passes_keywords_any(text: str, terms: List[str]) -> bool:
    return any(check_term_inclusion(text, t) for t in terms)


def test_chai_example_response_passes_relaxed_checks():
    # Beispiel: eval-chai-001 nach der Vereinfachung
    checks: Dict[str, Any] = {
        "must_include": ["freundlich"],
        "keywords_any": ["empathisch", "gern", "natürlich", "klar", "zugewandt", "zuwenden"],
        "not_include": ["Diagnose", "finanzieller Rat"],
    }
    # Eine plausible, freundliche und zugewandte Antwort
    response = (
        "Klar, gern! Klingt nach einem vollen Tag – erst einmal: du machst das gut. "
        "Wenn du magst, können wir kurz schauen, was dir jetzt freundlich und einfühlsam guttun könnte – "
        "vielleicht ein paar tiefe Atemzüge oder eine kleine Pause?"
    )
    text = response

    # must_include
    assert any(check_term_inclusion(text, term) for term in checks["must_include"])  # freundlich muss erkannt werden
    # keywords_any
    assert passes_keywords_any(text, checks["keywords_any"])  # mindestens eines (z.B. einfühlsam/zugewandt)
    # not_include
    assert not any(check_term_inclusion(text, term) for term in checks["not_include"])  # sollte keine verbotenen Begriffe enthalten


def test_synonyms_overlay_supports_empathie_variants():
    # Prüfe, dass Synonyme wie einfühlsam/zugewandt durch die Synonymlogik erfasst werden
    # Wir nutzen check_term_inclusion indirekt – hier sollte "einfühlsam" als Variante von empathisch zählen.
    text = "Dein Gefühl ist verständlich – ich versuche, ganz einfühlsam und zugewandt zu antworten."
    assert check_term_inclusion(text, "empathisch") is True

