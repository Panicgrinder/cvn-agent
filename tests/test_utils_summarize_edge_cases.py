from __future__ import annotations

from app.utils.summarize import extract_key_points, create_simple_summary, summarize_turn


def test_extract_key_points_empty_and_markers() -> None:
    assert extract_key_points("") == []
    text = "Wichtig ist, dass wir testen. Daher folgt ein Ergebnis. Und noch ein Satz."
    pts = extract_key_points(text, max_points=3)
    assert len(pts) >= 2
    assert any("wichtig" in p.lower() for p in pts)
    assert any("daher" in p.lower() for p in pts)


def test_create_simple_summary_truncation() -> None:
    msgs = [{"role": "user", "content": "x" * 200}]
    resp = "y" * 300
    s = create_simple_summary(msgs, resp)
    assert "..." in s  # Trunkierung aktiv
    assert "Nutzer fragte nach" in s and "Antwort:" in s


def test_summarize_turn_heuristic() -> None:
    msgs = [{"role": "user", "content": "Bitte fasse zusammen."}]
    resp = "Zusammenfassend ist wichtig, dass Tests stabil sind."
    out = summarize_turn(msgs, resp)
    assert isinstance(out.get("summary"), str)
    assert isinstance(out.get("keyfacts"), list)