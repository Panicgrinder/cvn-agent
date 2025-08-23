#!/usr/bin/env python
from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any, Dict

import httpx

# Projektwurzel dem Pfad hinzufügen, damit 'app' importierbar ist
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from app.main import app  # type: ignore
    from app.core.settings import settings  # type: ignore
except Exception as e:  # pragma: no cover
    raise SystemExit(f"Importfehler: {e}")


async def main() -> int:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://asgi") as client:
        # Health
        hr = await client.get("/health")
        print("HEALTH", hr.status_code, hr.json())

        # Chat
        payload: Dict[str, Any] = {
            "messages": [
                {"role": "user", "content": "Erkläre in 2 Sätzen was eine verkettete Liste ist."}
            ],
            "eval_mode": True,
            "options": {"host": settings.OLLAMA_HOST, "temperature": settings.TEMPERATURE},
        }
        cr = await client.post("/chat", json=payload)
        ct = cr.headers.get("content-type", "")
        print("CHAT", cr.status_code)
        if ct.startswith("application/json"):
            try:
                print(json.dumps(cr.json(), ensure_ascii=False))
            except Exception:
                print(cr.text)
        else:
            print(cr.text)
        return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
