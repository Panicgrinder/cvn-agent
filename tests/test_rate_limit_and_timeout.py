from __future__ import annotations

import os
import importlib
import asyncio
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_rate_limit_blocks_after_capacity(monkeypatch: pytest.MonkeyPatch) -> None:
    # Rate-Limit via ENV aktivieren und knappe Limits setzen; Trusted IPs leeren
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "2")
    monkeypatch.setenv("RATE_LIMIT_BURST", "0")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SEC", "5")
    monkeypatch.setenv("RATE_LIMIT_TRUSTED_IPS", "[]")

    # Settings und App frisch laden (damit Middleware hinzugefügt wird)
    settings_mod = importlib.reload(importlib.import_module("app.core.settings"))
    app_mod = importlib.reload(importlib.import_module("app.main"))
    app = app_mod.app

    client = TestClient(app)

    r1 = client.get("/")
    assert r1.status_code == 200
    r2 = client.get("/")
    assert r2.status_code == 200
    r3 = client.get("/")
    assert r3.status_code == 429
    # Rate-Limit-Header vorhanden
    assert r3.headers.get("Retry-After") is not None
    assert r3.headers.get("X-RateLimit-Limit") is not None
    assert r3.headers.get("X-RateLimit-Window") is not None


@pytest.mark.unit
def test_process_chat_timeout_returns_error_message(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx
    import app.api.chat as chat_module
    from app.api.models import ChatRequest

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self
        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False
        async def post(self, *args: Any, **kwargs: Any):
            # Simulierte Timeout-Exception
            raise httpx.ReadTimeout("timeout", request=httpx.Request("POST", "http://x"))

    def _factory(*args: Any, **kwargs: Any) -> Any:
        return _Client()

    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)

    req = ChatRequest(messages=[{"role": "user", "content": "Hallo"}])
    res = asyncio.run(chat_module.process_chat_request(req))
    assert "Fehler" in res.content or "Entschuldigung" in res.content
