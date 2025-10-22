from __future__ import annotations

import asyncio
import json
from typing import Callable, List

import pytest

import app.api.chat as chat_module
from app.api.models import ChatRequest


def _make_fake_stream_client(chunks: list[str]):
    class _Resp:
        status_code = 200
        def raise_for_status(self):
            return None
        async def aiter_lines(self):
            for c in chunks:
                yield json.dumps({"message": {"content": c}})
            yield json.dumps({"done": True})

    class _CM:
        async def __aenter__(self):
            return _Resp()
        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Client:
        def __init__(self, *a, **k):
            pass
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        def stream(self, *args, **kwargs):
            return _CM()

    return _Client()


@pytest.mark.streaming
def test_policy_stream_post_eval_rewrite(monkeypatch: pytest.MonkeyPatch):
    # Fake LLM stream producing one overly expressive chunk (RPG-ish)
    fake_factory: Callable[..., object] = lambda *a, **k: _make_fake_stream_client(["Ich: *nickt* Gerne helfe ich! :)"])  
    monkeypatch.setattr(chat_module.httpx, "AsyncClient", fake_factory)

    # Force policies enabled and eval settings for the test
    monkeypatch.setattr(chat_module.settings, "POLICIES_ENABLED", True, raising=False)
    monkeypatch.setattr(chat_module.settings, "EVAL_POST_REWRITE_ENABLED", True, raising=False)

    req = ChatRequest(messages=[{"role": "user", "content": "hi"}], options={"temperature": 0.1})
    agen = asyncio.run(chat_module.stream_chat_request(req, eval_mode=True))

    collected: List[str] = []
    async def _consume() -> None:
        async for s in agen:
            collected.append(s)
    asyncio.run(_consume())

    # Expect meta with rewritten
    assert any(s.startswith("event: meta") and '"policy_post": "rewritten"' in s for s in collected)
    # Expect a final delta line with a neutralized version (no role markers/emoji/exclamation)
    deltas = [s for s in collected if s.startswith("event: delta")]
    assert deltas, f"No delta event found: {collected}"
    assert ":)" not in deltas[-1] and "!" not in deltas[-1]
    assert "Ich:" not in deltas[-1] and "*nickt*" not in deltas[-1]
