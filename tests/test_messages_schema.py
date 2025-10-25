from __future__ import annotations

import asyncio
import pytest

import app.api.chat as chat_module
from app.api.models import ChatRequest, ChatMessage


class _Resp:
    status_code = 200
    def raise_for_status(self):
        return None
    def json(self):
        return {"message": {"content": "ok"}}


class _Client:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def post(self, url, json, headers):
        return _Resp()


def _patch_client(monkeypatch: pytest.MonkeyPatch) -> None:
    def _factory(*a: object, **k: object) -> _Client:
        return _Client()
    monkeypatch.setattr(chat_module.httpx, "AsyncClient", _factory)


@pytest.mark.unit
@pytest.mark.api
def test_chatrequest_accepts_dict_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch)
    req = ChatRequest(messages=[{"role": "user", "content": "Hallo"}])
    resp = asyncio.run(chat_module.process_chat_request(req))
    assert resp.content == "ok"


@pytest.mark.unit
@pytest.mark.api
def test_chatrequest_accepts_object_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch)
    msg = ChatMessage(role="user", content="Hallo")
    req = ChatRequest(messages=[msg])
    resp = asyncio.run(chat_module.process_chat_request(req))
    assert resp.content == "ok"
