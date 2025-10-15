from __future__ import annotations

import httpx
from typing import Any, Dict, List
import asyncio
from pytest import MonkeyPatch

from app.api.models import ChatMessage, ChatResponse

# Nur wenn der LLM-Client existiert
try:
    from app.services.llm import generate_reply
except Exception:  # pragma: no cover
    generate_reply = None  # type: ignore


def _client_with_mock(response_payload: Dict[str, Any]) -> httpx.AsyncClient:
    async def _handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/api/chat"):
            return httpx.Response(200, json=response_payload)
        return httpx.Response(404)

    transport = httpx.MockTransport(_handler)
    return httpx.AsyncClient(transport=transport)


def test_generate_reply_with_mock_transport(monkeypatch: MonkeyPatch) -> None:
    if generate_reply is None:
        return

    payload = {"message": {"role": "assistant", "content": "Hallo Welt"}}

    client = _client_with_mock(payload)

    # monkeypatch the AsyncClient constructor to provide our mock
    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        return client

    monkeypatch.setattr(httpx, "AsyncClient", _factory)

    msgs: List[ChatMessage] = [ChatMessage(role="user", content="hi")]

    res: ChatResponse = asyncio.run(generate_reply(msgs))
    assert isinstance(res, ChatResponse)
    assert "Hallo Welt" in res.content
