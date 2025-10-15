from __future__ import annotations

import asyncio
import json

from pytest import MonkeyPatch
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
@pytest.mark.api
def test_stream_chat_sends_sse_chunks_and_done(monkeypatch: MonkeyPatch) -> None:
    from typing import Callable
    fake_factory: Callable[..., object] = lambda *a, **k: _make_fake_stream_client(["a", "b"])  
    monkeypatch.setattr(chat_module.httpx, "AsyncClient", fake_factory)
    req = ChatRequest(messages=[{"role": "user", "content": "hi"}])
    agen = asyncio.run(chat_module.stream_chat_request(req))

    collected: list[str] = []
    async def _consume():
        async for s in agen:
            collected.append(s)

    asyncio.run(_consume())

    assert any("data: a" in s for s in collected)
    assert any("data: b" in s for s in collected)
    assert any(s.startswith("event: done") for s in collected)
