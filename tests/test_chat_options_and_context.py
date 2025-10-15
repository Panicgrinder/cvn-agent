from __future__ import annotations

import json
from typing import Any, Dict, List, cast

import httpx
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.main import app
import app.api.chat as chat_module
from app.core import settings as settings_module


# Echten AsyncClient sichern, bevor gepatcht wird
RealAsyncClient = httpx.AsyncClient


def _mock_async_client_capture(payload_box: Dict[str, Any]) -> httpx.AsyncClient:
    async def _handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/api/chat"):
            try:
                data = json.loads(request.content.decode("utf-8"))
            except Exception:
                data = {}
            payload_box["last"] = data
            return httpx.Response(200, json={
                "message": {"role": "assistant", "content": "ok"}
            })
        return httpx.Response(404)

    transport = httpx.MockTransport(_handler)
    return RealAsyncClient(transport=transport)


def test_chat_applies_top_p_and_temperature_cap(monkeypatch: MonkeyPatch) -> None:
    payload_box: Dict[str, Any] = {}

    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        return _mock_async_client_capture(payload_box)

    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)

    client = TestClient(app)
    resp = client.post(
        "/chat",
        json={
            "messages": [{"role": "user", "content": "hi"}],
            "eval_mode": True,
            "options": {"temperature": 0.8, "top_p": 0.9, "num_predict": 999999},
        },
    )
    assert resp.status_code == 200

    sent = cast(Dict[str, Any], payload_box.get("last") or {})
    opts = cast(Dict[str, Any], sent.get("options", {}))
    # Temperatur sollte im Eval-Modus gedeckelt sein
    temp_val = opts.get("temperature")
    assert temp_val is not None and float(temp_val) <= 0.25
    # top_p sollte übernommen sein
    assert opts.get("top_p") == 0.9
    # num_predict sollte auf SETTINGS.REQUEST_MAX_TOKENS gedeckelt sein
    from app.core.settings import settings
    assert 1 <= int(opts.get("num_predict", 0)) <= settings.REQUEST_MAX_TOKENS


def test_chat_injects_context_notes_when_enabled(monkeypatch: MonkeyPatch) -> None:
    payload_box: Dict[str, Any] = {}

    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        return _mock_async_client_capture(payload_box)

    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)
    # Kontext-Notizen aktivieren und Funktion stubben
    monkeypatch.setattr(settings_module.settings, "CONTEXT_NOTES_ENABLED", True, raising=False)
    from typing import Iterable
    def _stub_load_context_notes(paths: Iterable[str], max_chars: int = 4000) -> str:
        return "CTX-NOTES"
    monkeypatch.setattr(chat_module, "load_context_notes", _stub_load_context_notes)

    client = TestClient(app)
    resp = client.post(
        "/chat",
        json={"messages": [{"role": "user", "content": "frage"}]},
    )
    assert resp.status_code == 200

    sent = cast(Dict[str, Any], payload_box.get("last") or {})
    msgs = cast(List[Dict[str, str]], sent.get("messages", []))
    # Erwartet: [0] system default, [1] Kontext-Notizen
    assert msgs and msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "system"
    assert "Kontext-Notizen" in msgs[1]["content"] and "CTX-NOTES" in msgs[1]["content"]
