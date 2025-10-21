from __future__ import annotations

import asyncio
import json
from typing import Callable

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
def test_policy_stream_post_rewrite(monkeypatch):
    # Fake LLM stream producing two chunks
    fake_factory: Callable[..., object] = lambda *a, **k: _make_fake_stream_client(["foo", "bar"])  
    monkeypatch.setattr(chat_module.httpx, "AsyncClient", fake_factory)

    # Monkeypatch post-policy to force rewrite
    def fake_apply_post(text: str, *, mode: str = "default", profile_id=None):
        class R:
            action = "rewrite"
            def __init__(self, t: str) -> None:
                self.text = t.upper()
        return R(text)
    monkeypatch.setattr(chat_module, "apply_post", fake_apply_post)

    req = ChatRequest(messages=[{"role": "user", "content": "hi"}])
    agen = asyncio.run(chat_module.stream_chat_request(req))

    collected: list[str] = []
    async def _consume():
        async for s in agen:
            collected.append(s)
    asyncio.run(_consume())

    # Expect original chunks "foo" and "bar"
    assert any("data: foo" in s for s in collected)
    assert any("data: bar" in s for s in collected)
    # Expect meta with rewritten and a delta with the uppercase
    assert any(s.startswith("event: meta") and '"policy_post": "rewritten"' in s for s in collected)
    assert any(s.startswith("event: delta") and '"text": "FOOBAR"' in s for s in collected)
    assert any(s.startswith("event: done") for s in collected)
