from __future__ import annotations

import importlib
import pytest
from fastapi.testclient import TestClient


@pytest.mark.api
def test_chat_post_internal_error_sets_header(monkeypatch: pytest.MonkeyPatch) -> None:
    app_mod = importlib.import_module("app.main")
    app = app_mod.app
    # Patch process_chat_request in the module where it's imported
    from typing import Any, NoReturn
    async def _boom(*_a: Any, **_k: Any) -> NoReturn:
        raise RuntimeError("boom")
    monkeypatch.setattr(app_mod, "process_chat_request", _boom)

    client = TestClient(app)
    payload = {"messages": [{"role": "user", "content": "hi"}]}
    r = client.post("/chat", json=payload)
    assert r.status_code == 500
    assert r.headers.get("X-Request-ID")
    assert "Interner Serverfehler" in r.text or "detail" in r.json()
