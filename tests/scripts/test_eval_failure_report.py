from __future__ import annotations

import importlib
from typing import List, Dict, Any


def _mk_result(ok: bool, pkg: str, iid: str, reasons: List[str], response: str = "") -> Any:
    run_eval = importlib.import_module("scripts.run_eval")
    return run_eval.EvaluationResult(
        item_id=iid,
        response=response,
        checks_passed={},
        success=ok,
        failed_checks=list(reasons),
        source_file=None,
        source_package=pkg,
        duration_ms=0,
        attempts=1,
    )


def test_compute_failure_summary_counts_and_terms() -> None:
    run_eval = importlib.import_module("scripts.run_eval")

    results = [
        _mk_result(False, "pkgA", "id-1", ["Erforderlicher Begriff nicht gefunden: 'freundlich'"]),
        _mk_result(False, "pkgA", "id-2", ["Erforderlicher Begriff nicht gefunden: 'freundlich'"]),
        _mk_result(False, "pkgA", "id-3", ["Antwort im RPG-Modus, aber Test erwartet allgemeine Antwort"]),
        _mk_result(True,  "pkgA", "id-4", []),
        _mk_result(False, "pkgB", "id-5", ["Erforderlicher Begriff nicht gefunden: 'kurz'"]),
        _mk_result(False, "pkgB", "id-6", ["Erforderlicher Begriff nicht gefunden: 'empathisch'"]),
    ]

    summary: Dict[str, Any] = run_eval.compute_failure_summary(results)
    assert summary["total"] == 6
    assert summary["successes"] == 1
    # 2x freundlich, 1x kurz, 1x empathisch
    top = dict(summary["top_missing_terms"])  # type: ignore[arg-type]
    assert top.get("freundlich") == 2
    # 4 Einträge haben Term-Inklusionsfehler (id-1, id-2, id-5, id-6)
    assert summary["fail_counts"]["term_inclusion"] == 4
    assert summary["fail_counts"]["rpg_style"] == 1
    # per-package listing present
    assert "pkgA" in summary["per_package_fails"]
    assert "pkgB" in summary["per_package_fails"]
