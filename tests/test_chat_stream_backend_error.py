from __future__ import annotations

from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

import app.api.chat as chat_module
from app.main import app


RealAsyncClient = httpx.AsyncClient


def _mock_async_client_error() -> httpx.AsyncClient:
    async def _handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/api/chat"):
            return httpx.Response(500, json={"error": "backend"}, request=request)
        return httpx.Response(404)

    transport = httpx.MockTransport(_handler)
    return RealAsyncClient(transport=transport)


@pytest.mark.api
@pytest.mark.unit
def test_chat_stream_backend_error(monkeypatch: "pytest.MonkeyPatch") -> None:
    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:  # noqa: ARG001
        return _mock_async_client_error()

    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)

    client = TestClient(app)
    resp = client.post("/chat/stream", json={
        "messages": [{"role": "user", "content": "hi"}],
        "eval_mode": True
    })
    assert resp.status_code == 200
    text = resp.text
    assert "event: error" in text or "error" in text.lower()
