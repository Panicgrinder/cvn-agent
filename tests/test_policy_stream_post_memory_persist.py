from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Callable, List

import pytest

import app.api.chat as chat_module
from app.api.models import ChatRequest
from app.core.memory import get_memory_store


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
def test_policy_stream_post_memory_persist(monkeypatch):
    # Fake LLM stream producing two chunks
    fake_factory: Callable[..., object] = lambda *a, **k: _make_fake_stream_client(["foo", "bar"])  
    monkeypatch.setattr(chat_module.httpx, "AsyncClient", fake_factory)

    # Monkeypatch post-policy to force rewrite to uppercase
    def fake_apply_post(text: str, *, mode: str = "default", profile_id=None):
        # Return object with attributes expected by the handler
        return SimpleNamespace(action="rewrite", text=text.upper())
    monkeypatch.setattr(chat_module, "apply_post", fake_apply_post)

    sid = "mem-check-1"
    req = ChatRequest(messages=[{"role": "user", "content": "hi"}], session_id=sid)
    agen = asyncio.run(chat_module.stream_chat_request(req))

    async def _consume() -> List[str]:
        out: List[str] = []
        async for s in agen:
            out.append(s)
        return out
    _ = asyncio.run(_consume())

    # Verify memory persists the post-processed final text (FOOBAR)
    async def _check():
        store = get_memory_store()
        window = await store.get_window(sid, max_chars=10000, max_turns=100)
        # Search for last assistant message
        assistants = [m for m in window if m.get("role") == "assistant"]
        assert assistants, f"No assistant messages found in memory for session {sid}"
        assert assistants[-1].get("content") == "FOOBAR"

    asyncio.run(_check())
