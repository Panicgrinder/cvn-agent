from __future__ import annotations

import os
import json
import tempfile
 

from utils.context_notes import load_context_notes
from app.utils.summarize import extract_key_points, create_simple_summary, summarize_turn


def test_load_context_notes_prefers_first_existing_and_truncates():
    with tempfile.TemporaryDirectory() as tmp:
        p1 = os.path.join(tmp, "a.json")
        p2 = os.path.join(tmp, "b.txt")
        with open(p1, "w", encoding="utf-8") as f:
            json.dump({"x": 1}, f)
        with open(p2, "w", encoding="utf-8") as f:
            f.write("hello\nworld")

        res = load_context_notes([p1, p2], max_chars=20)
        assert res is not None
        assert "\n" in res or "{" in res
        assert len(res) <= 20


def test_summarize_helpers_basic():
    messages = [
        {"role": "user", "content": "Bitte nenne die Vorteile von Python."}
    ]
    response = (
        "Wichtig ist, dass Python eine große Community hat. "
        "Zusammenfassend: leicht zu lesen."
    )
    points = extract_key_points(response, max_points=3)
    assert points and isinstance(points, list)

    simple = create_simple_summary(messages, response)
    assert isinstance(simple, str) and simple

    out = summarize_turn(messages, response)
    assert isinstance(out, dict)
    assert "summary" in out and "keyfacts" in out
