from __future__ import annotations

from typing import Any, Dict
from fastapi.testclient import TestClient
import pytest

import app.api.chat as chat_module
from app.main import app


def _fake_client_factory():
    class _Resp:
        status_code = 200
        def json(self) -> Dict[str, Any]:
            return {"message": {"content": "ok"}}
        def raise_for_status(self) -> None:
            return

    class _Client:
        async def __aenter__(self):
            return self
        async def __aexit__(self, exc_type, exc, tb):
            return False
        async def post(self, url: str, json: Dict[str, Any], headers: Dict[str, str]):
            # Sicherstellen, dass Systemprompt als erste Nachricht gesetzt wird
            assert json["messages"][0]["role"] == "system"
            return _Resp()

    return _Client


@pytest.mark.api
@pytest.mark.unit
def test_chat_post_endpoint_happy(monkeypatch: pytest.MonkeyPatch) -> None:
    # httpx.AsyncClient in process_chat_request stubben
    import httpx
    monkeypatch.setattr(httpx, "AsyncClient", lambda *a, **k: _fake_client_factory()())

    client = TestClient(app)
    payload: Dict[str, Any] = {
        "messages": [{"role": "user", "content": "hi"}],
        "options": {"temperature": 0.5},
    }
    resp = client.post("/chat", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("content") == "ok"
