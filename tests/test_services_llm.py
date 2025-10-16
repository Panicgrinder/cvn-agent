from __future__ import annotations

import asyncio
from typing import Any, Dict

import pytest


@pytest.mark.unit
def test_generate_reply_success_and_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx
    from app.services.llm import generate_reply
    from app.api.models import ChatMessage

    class _OKResp:
        status_code = 200
        def raise_for_status(self) -> None:
            return
        def json(self) -> Dict[str, Any]:
            return {"message": {"content": "hi"}}

    class _ErrResp:
        def raise_for_status(self) -> None:
            raise httpx.HTTPStatusError("boom", request=httpx.Request("POST", "http://x"), response=httpx.Response(500))

    class _ClientOK:
        async def __aenter__(self) -> "_ClientOK":
            return self
        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False
        async def post(self, *args: Any, **kwargs: Any):
            return _OKResp()

    class _ClientHTTPError:
        async def __aenter__(self) -> "_ClientHTTPError":
            return self
        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False
        async def post(self, *args: Any, **kwargs: Any):
            return _ErrResp()

    # Success
    def _factory_ok(*a: Any, **k: Any) -> Any:
        return _ClientOK()
    monkeypatch.setattr(httpx, "AsyncClient", _factory_ok)
    ok = asyncio.run(generate_reply([ChatMessage(role="user", content="hi")]))
    assert ok.content == "hi"

    # HTTPStatusError
    def _factory_http_err(*a: Any, **k: Any) -> Any:
        return _ClientHTTPError()
    monkeypatch.setattr(httpx, "AsyncClient", _factory_http_err)
    http_err = asyncio.run(generate_reply([ChatMessage(role="user", content="hi")]))
    assert "HTTP-Fehler" in http_err.content

    # RequestError
    class _ClientReqErr:
        async def __aenter__(self) -> "_ClientReqErr":
            return self
        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False
        async def post(self, *args: Any, **kwargs: Any):
            raise httpx.RequestError("nope")

    def _factory_req_err(*a: Any, **k: Any) -> Any:
        return _ClientReqErr()
    monkeypatch.setattr(httpx, "AsyncClient", _factory_req_err)
    req_err = asyncio.run(generate_reply([ChatMessage(role="user", content="hi")]))
    assert "Verbindung" in req_err.content


@pytest.mark.unit
def test_generate_completion_success(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx
    from app.services.llm import generate_completion

    class _Resp:
        status_code = 200
        def raise_for_status(self) -> None:
            return
        def json(self) -> Dict[str, Any]:
            return {"response": "done"}

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self
        async def __aexit__(self, exc_type, exc, tb) -> bool:
            return False
        async def post(self, *args: Any, **kwargs: Any):
            return _Resp()

    def _factory(*a: Any, **k: Any) -> Any:
        return _Client()
    monkeypatch.setattr(httpx, "AsyncClient", _factory)
    out = asyncio.run(generate_completion("ping", options={"temperature": 0.1}))
    assert out == "done"