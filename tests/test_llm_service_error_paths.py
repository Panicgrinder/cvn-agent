from __future__ import annotations

import httpx
import asyncio
from typing import Any
from pytest import MonkeyPatch

from app.services import llm as llm_module
from app.api.models import ChatMessage

# Originalreferenz sichern, bevor wir etwas patchen
RealAsyncClient = httpx.AsyncClient


def _async_client_raise_status(status_code: int) -> httpx.AsyncClient:
    async def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "x"})

    return RealAsyncClient(transport=httpx.MockTransport(_handler))


def _async_client_request_error(exc: Exception) -> httpx.AsyncClient:
    async def _handler(request: httpx.Request) -> httpx.Response:
        raise exc

    return RealAsyncClient(transport=httpx.MockTransport(_handler))


def test_generate_reply_http_status_error(monkeypatch: MonkeyPatch) -> None:
    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        return _async_client_raise_status(500)

    monkeypatch.setattr(llm_module.httpx, "AsyncClient", _factory)

    msgs = [ChatMessage(role="user", content="hi")]
    res = asyncio.run(llm_module.generate_reply(msgs))
    assert "HTTP-Fehler" in res.content


def test_generate_reply_request_error(monkeypatch: MonkeyPatch) -> None:
    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        return _async_client_request_error(httpx.ConnectError("nope", request=httpx.Request("POST", "http://x")))

    monkeypatch.setattr(llm_module.httpx, "AsyncClient", _factory)

    msgs = [ChatMessage(role="user", content="hi")]
    res = asyncio.run(llm_module.generate_reply(msgs))
    assert "Verbindung" in res.content or "fehlgeschlagen" in res.content
