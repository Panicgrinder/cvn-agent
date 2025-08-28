from __future__ import annotations

import json
from typing import Any, Dict, List, cast

import httpx
from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from app.main import app
from app.core import prompts
import app.api.chat as chat_module

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
            # minimal gültige Antwortstruktur für process_chat_request
            return httpx.Response(200, json={
                "message": {"role": "assistant", "content": "ok"}
            })
        return httpx.Response(404)

    transport = httpx.MockTransport(_handler)
    return RealAsyncClient(transport=transport)


def test_chat_injects_default_system_prompt(monkeypatch: MonkeyPatch) -> None:
    payload_box: Dict[str, Any] = {}

    # Patch nur im Modul app.api.chat anwenden, um Rekursion zu vermeiden
    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        return _mock_async_client_capture(payload_box)

    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)

    client = TestClient(app)
    resp = client.post("/chat", json={
        "messages": [{"role": "user", "content": "hi"}]
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("content") == "ok"

    sent_any = cast(Dict[str, Any], payload_box.get("last") or {})
    assert isinstance(sent_any, dict)
    msgs_any = cast(List[Dict[str, Any]], sent_any.get("messages", []))
    assert isinstance(msgs_any, list)
    msgs: List[Dict[str, str]] = [cast(Dict[str, str], m) for m in msgs_any]
    assert msgs, "Es wurden keine Nachrichten an das LLM gesendet"
    assert msgs[0]["role"] == "system"
    assert msgs[0]["content"] == prompts.DEFAULT_SYSTEM_PROMPT


def test_chat_injects_eval_system_prompt(monkeypatch: MonkeyPatch) -> None:
    payload_box: Dict[str, Any] = {}

    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        return _mock_async_client_capture(payload_box)

    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)

    client = TestClient(app)
    resp = client.post("/chat", json={
        "messages": [{"role": "user", "content": "frage"}],
        "eval_mode": True
    })
    assert resp.status_code == 200

    sent_any = cast(Dict[str, Any], payload_box.get("last") or {})
    assert isinstance(sent_any, dict)
    msgs_any = cast(List[Dict[str, Any]], sent_any.get("messages", []))
    assert isinstance(msgs_any, list)
    msgs: List[Dict[str, str]] = [cast(Dict[str, str], m) for m in msgs_any]
    assert msgs and msgs[0]["role"] == "system"
    assert msgs[0]["content"] == prompts.EVAL_SYSTEM_PROMPT


def test_chat_injects_unrestricted_system_prompt(monkeypatch: MonkeyPatch) -> None:
    payload_box: Dict[str, Any] = {}

    def _factory(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
        return _mock_async_client_capture(payload_box)

    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)

    client = TestClient(app)
    resp = client.post("/chat", json={
        "messages": [{"role": "user", "content": "frage"}],
        "unrestricted_mode": True
    })
    assert resp.status_code == 200

    sent_any = cast(Dict[str, Any], payload_box.get("last") or {})
    assert isinstance(sent_any, dict)
    msgs_any = cast(List[Dict[str, Any]], sent_any.get("messages", []))
    assert isinstance(msgs_any, list)
    msgs: List[Dict[str, str]] = [cast(Dict[str, str], m) for m in msgs_any]
    assert msgs and msgs[0]["role"] == "system"
    assert msgs[0]["content"] == prompts.UNRESTRICTED_SYSTEM_PROMPT
