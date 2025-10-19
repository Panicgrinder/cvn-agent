from __future__ import annotations

import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.mark.streaming
def test_chat_stream_internal_error_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    app_mod = importlib.import_module("app.main")
    app = app_mod.app

    # Patch the imported symbol in app.main to return an SSE error generator
    from typing import Any, AsyncIterator
    async def _sse_error(*_a: Any, **_k: Any) -> AsyncIterator[bytes]:
        async def _agen() -> AsyncIterator[bytes]:
            yield b"event: error\ndata: boom\n\n"
        return _agen()
    monkeypatch.setattr(app_mod, "stream_chat_request", _sse_error)

    client = TestClient(app)
    payload = {"messages": [{"role": "user", "content": "hi"}]}
    r = client.post("/chat/stream", json=payload)
    assert r.status_code == 200
    assert r.headers.get("X-Request-ID")
    assert "event: error" in r.text