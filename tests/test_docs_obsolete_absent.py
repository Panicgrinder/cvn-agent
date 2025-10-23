from __future__ import annotations

import os


def test_agent_prompt_is_deprecated_stub():
    path = os.path.join(os.getcwd(), "docs", "AGENT_PROMPT.md")
    # Erlaubt: Datei fehlt (automatische Bereinigung) ODER existiert als Stub mit Hinweis
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        assert "Obsolet" in text and "AGENT_BEHAVIOR.md" in text
    else:
        # Datei ist bewusst entfernt – das ist OK
        assert True


def test_no_nested_cvn_agent_dir_tracked():
    # Sicherstellen, dass versehentliches /cvn-agent/ nicht in Git getrackt wird
    # (Existenz lokal ist egal; .gitignore sollte es ausschließen)
    nested = os.path.join(os.getcwd(), "cvn-agent")
    # Wenn der Ordner existiert, muss er leer oder nur ignorierte Inhalte enthalten.
    # Wir testen minimal: er darf keine docs/AGENT_PROMPT.md Kopie enthalten.
    suspect = os.path.join(nested, "docs", "AGENT_PROMPT.md")
    assert not os.path.exists(suspect), "Verschachtelte Kopie von AGENT_PROMPT.md gefunden; bitte Ordner entfernen."
