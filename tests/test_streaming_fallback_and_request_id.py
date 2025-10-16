from __future__ import annotations

import asyncio
import json
from typing import Any

import pytest

import app.api.chat as chat_module
from app.api.models import ChatRequest


@pytest.mark.streaming
@pytest.mark.api
def test_streaming_fallback_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Resp:
        status_code = 200
        def raise_for_status(self) -> None:
            return
        async def aiter_lines(self):
            yield "{this is not json}"
            yield json.dumps({"done": True})

    class _CM:
        async def __aenter__(self):
            return _Resp()
        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Client:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        def stream(self, *args: Any, **kwargs: Any):
            return _CM()

    monkeypatch.setattr(chat_module.httpx, "AsyncClient", lambda *a, **k: _Client())

    req = ChatRequest(messages=[{"role": "user", "content": "hi"}])
    agen = asyncio.run(chat_module.stream_chat_request(req))

    collected: list[str] = []
    async def _consume():
        async for s in agen:
            collected.append(s)

    asyncio.run(_consume())
    # Fallback sollte den rohen Inhalt als data senden
    assert any("data: {this is not json}" in s for s in collected)
    assert any(s.startswith("event: done") for s in collected)


@pytest.mark.api
def test_request_id_header_propagation(monkeypatch: pytest.MonkeyPatch) -> None:
    from fastapi.testclient import TestClient
    import importlib

    captured_headers: dict[str, str] = {}

    import httpx
    import app.api.chat as chat_module

    class _Resp:
        status_code = 200
        def raise_for_status(self) -> None:
            return
        def json(self):
            return {"message": {"content": "ok"}}

    class _Client:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def post(self, url, json, headers):
            captured_headers.update(headers)
            return _Resp()

    def _factory(*a, **k):
        return _Client()
    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)

    # Rate-Limiter deaktivieren und App frisch laden
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "false")
    importlib.reload(importlib.import_module("app.core.settings"))
    app_mod = importlib.reload(importlib.import_module("app.main"))
    app = app_mod.app
    client = TestClient(app)
    resp = client.post("/chat", json={"messages": [{"role": "user", "content": "hi"}]})
    assert resp.status_code == 200
    # Middleware sollte Request-ID setzen und diese wird propagiert
    req_id = resp.headers.get("X-Request-ID")
    assert req_id and captured_headers.get("X-Request-ID") == req_id
