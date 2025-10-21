import json
import asyncio
from typing import Any, Dict

import pytest

from scripts.run_eval import run_evaluation, EvaluationItem


@pytest.mark.asyncio
async def test_cli_like_asgi_smoke_with_hint(monkeypatch):
    # Minimal ein Item, das must_include hat, damit compute_hint_terms etwas findet
    item = EvaluationItem(
        id="eval-zzz-001",
        messages=[{"role": "user", "content": "Bitte antworte sehr kurz."}],
        checks={
            "must_include": ["probe"],
            "keywords_any": [],
            "keywords_at_least": {"count": 0, "items": []},
            "not_include": [],
            "regex": [],
        },
        source_file="fixture.jsonl",
        source_package="fixture",
    )

    async def _fake_loader(_patterns):
        return [item]

    # monkeypatch load_evaluation_items to return our single fixture
    from scripts import run_eval as _runner
    monkeypatch.setattr(_runner, "load_evaluation_items", _fake_loader)

    # asgi=True verwendet httpx.ASGITransport gegen app.main:app
    results = await run_evaluation(
        patterns=["dummy"],
        api_url="http://localhost:8000/chat",
        eval_mode=True,
        skip_preflight=True,
        asgi=True,
        enabled_checks=["must_include"],
        quiet=True,
        retries=0,
        use_cache=False,
        hint_must_include=True,
    )

    # Wir erwarten Ergebnisse (der Test prüft in der Praxis, dass der Runner die Pipeline durchläuft)
    assert isinstance(results, list)

    # Zusätzlich: Der Runner sollte im quiet-Mode eine Statuszeile ausgeben, das prüfen wir indirekt,
    # indem wir compute_hint_terms greift (weil must_include gesetzt) -> logs sind nicht trivial abzugreifen hier.
