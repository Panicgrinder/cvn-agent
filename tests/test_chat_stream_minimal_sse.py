from __future__ import annotations

import json
import httpx
import pytest

from app.main import app
from app.core.settings import settings


@pytest.mark.api
@pytest.mark.unit
@pytest.mark.asyncio
async def test_chat_stream_minimal_asgi() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://asgi") as client:
        from typing import Dict, Any
        payload: Dict[str, Any] = {
            "messages": [{"role": "user", "content": "Sag Hallo"}],
            "eval_mode": True,
            "options": {"host": settings.OLLAMA_HOST}
        }
        resp = await client.post("/chat/stream", json=payload)
        # 200 OK, Body enthält SSE/Text; wir prüfen nur Status
        assert resp.status_code == 200
