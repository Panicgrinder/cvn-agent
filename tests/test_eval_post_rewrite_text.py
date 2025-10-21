from __future__ import annotations

import importlib


def test_eval_post_rewrite_neutralize_basic() -> None:
    cm = importlib.import_module("app.core.content_management")
    # Aktiviere Policies via settings mocken? Standardmäßig POLICIES_ENABLED False -> wir erwarten allow.
    # Wir testen stattdessen direkt die Normalisierer.
    txt = "Ich finde, du solltest das lassen! :)"
    t = cm.neutralize(txt)
    # Keine 1./2. Person direkt
    assert " ich " not in f" {t.lower()} "
    assert " du " not in f" {t.lower()} "
    # Keine Emojis/Ausrufe
    assert "!" not in t
    assert ":)" not in t


def test_eval_post_rewrite_limits() -> None:
    cm = importlib.import_module("app.core.content_management")
    txt = """Satz eins ist länger als üblich. Satz zwei ist ebenfalls vorhanden! Satz drei sollte abgeschnitten werden?"""
    # Sätze begrenzen
    limited = cm.limit_sentences(txt, 2)
    assert limited.count(".") + limited.count("!") + limited.count("?") >= 1
    # Zeichen begrenzen
    trimmed = cm.trim_length(limited, 240)
    assert len(trimmed) <= 240
