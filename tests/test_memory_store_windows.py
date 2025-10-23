from __future__ import annotations

from pathlib import Path

import pytest

from app.core.memory import InMemoryStore, JsonlStore


@pytest.mark.asyncio
async def test_inmemory_window_and_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    store = InMemoryStore()
    sid = "s1"
    # Append over limits
    for _ in range(10):
        await store.append(sid, "user", "x" * 50)
    # Window should respect limits: default settings are enforced at append
    win = await store.get_window(sid, max_chars=200, max_turns=3)
    # max_turns=3 => 3 messages max
    assert len(win) <= 3
    # Ensure left-truncate by content check: recent content remains
    # Append a marker and check it's present
    await store.append(sid, "assistant", "MARKER")
    win2 = await store.get_window(sid, max_chars=200, max_turns=3)
    assert any(m["content"].endswith("MARKER") for m in win2)


@pytest.mark.asyncio
async def test_jsonl_window_and_truncation(tmp_path: Path) -> None:
    base = tmp_path / "mem"
    store = JsonlStore(base_dir=base)
    sid = "s2"
    # Append 6 turns
    for i in range(6):
        await store.append(sid, "user", f"turn_{i}_" + ("y" * 40))
    # Window should be computed on read
    win = await store.get_window(sid, max_chars=120, max_turns=4)
    # at most 4 turns
    assert len(win) <= 4
    # left-truncate by chars: earliest items trimmed
    contents = [m["content"] for m in win]
    assert any("turn_5_" in c for c in contents)
    # ensure file exists
    assert (base / f"session_{sid}.jsonl").exists()
