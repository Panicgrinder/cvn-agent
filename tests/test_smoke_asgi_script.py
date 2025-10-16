from __future__ import annotations

import asyncio
import pytest


@pytest.mark.scripts
@pytest.mark.unit
def test_smoke_asgi_main_executes() -> None:
    # Import sollte funktionieren; main() liefert int-Exitcode
    from scripts import smoke_asgi as s

    async def _run() -> int:
        # Wir patchen nichts: httpx.ASGITransport ruft die In-Process-App auf
        return await s.main()

    rc = asyncio.run(_run())
    assert isinstance(rc, int)
    assert rc == 0
