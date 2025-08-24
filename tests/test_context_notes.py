import os
import unittest
from unittest.mock import patch
from typing import Any, Dict, List, cast

from app.api.models import ChatRequest
from app.api.chat import process_chat_request


class _ResponseStub:
    status_code = 200
    def raise_for_status(self):
        return None
    def json(self):
        return {"message": {"content": "OK"}}


class _CaptureClient:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return None
    async def post(self, url, json, headers=None):
        return _ResponseStub()


class TestContextNotes(unittest.IsolatedAsyncioTestCase):
    async def _capture_messages(self, req: ChatRequest) -> List[Dict[str, Any]]:
        sent_payload: Dict[str, Any] = {}

        class Client(_CaptureClient):
            async def post(self, url, json, headers=None):
                nonlocal sent_payload
                sent_payload = cast(Dict[str, Any], json)
                return _ResponseStub()

        with patch("app.api.chat.httpx.AsyncClient", Client):
            await process_chat_request(req, eval_mode=False, unrestricted_mode=False)
        return cast(List[Dict[str, Any]], sent_payload.get("messages") or [])

    async def test_injects_notes_when_enabled(self):
        # Lege eine temporäre Datei an
        tmp_dir = os.path.join("eval", "config")
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_file = os.path.join(tmp_dir, "context.local.md")
        with open(tmp_file, "w", encoding="utf-8") as f:
            f.write("Kontext-Testnotiz")

        req = ChatRequest(messages=[{"role": "user", "content": "Ping"}])

        with patch("app.core.settings.settings.CONTEXT_NOTES_ENABLED", True), \
             patch("app.core.settings.settings.CONTEXT_NOTES_PATHS", [tmp_file]), \
             patch("app.core.settings.settings.CONTEXT_NOTES_MAX_CHARS", 200):
            messages = await self._capture_messages(req)

        # Erwartung: [0] system (Default Prompt), [1] system (Notizen), [..., last] user
        assert len(messages) >= 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "system"
        assert "Kontext-Testnotiz" in str(messages[1].get("content"))
