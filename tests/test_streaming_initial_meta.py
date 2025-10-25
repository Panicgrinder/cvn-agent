from __future__ import annotations

import asyncio
import json
from typing import Any, List

import pytest

import app.api.chat as chat_module
from app.api.models import ChatRequest


class _Resp:
    status_code = 200
    def raise_for_status(self) -> None:
        return
    async def aiter_lines(self):
        # minimal stream: no content chunks, just done
        yield json.dumps({"done": True})


class _CM:
    async def __aenter__(self):
        return _Resp()
    async def __aexit__(self, exc_type, exc, tb):
        return False


class _Client:
    def __init__(self, *a: Any, **k: Any):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    def stream(self, *args: Any, **kwargs: Any):
        return _CM()


@pytest.mark.streaming
@pytest.mark.api
def test_initial_meta_event_emitted(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure our fake client is used
    def _factory(*a: object, **k: object) -> _Client:
        return _Client()
    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)

    req = ChatRequest(messages=[{"role": "user", "content": "hi"}])
    agen = asyncio.run(chat_module.stream_chat_request(req, eval_mode=False, unrestricted_mode=False))

    events: List[str] = []

    async def _consume() -> None:
        async for s in agen:
            events.append(s)

    asyncio.run(_consume())

    assert events, "No events received from stream"
    # First event should be a meta with params and default mode
    first = events[0]
    assert first.startswith("event: meta"), f"First event not meta: {first}"
    assert '"params"' in first and '"mode": "default"' in first
    # And stream must still end with done
    assert any(e.startswith("event: done") for e in events)
