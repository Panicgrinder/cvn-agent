from __future__ import annotations

import asyncio
import json
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Dict, Iterable, List, Mapping, Optional

from .settings import settings


@dataclass
class _Turn:
    role: str
    content: str

    def to_message(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class MemoryStore:
    async def append(self, session_id: str, role: str, content: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError

    async def get_window(self, session_id: str, max_chars: int, max_turns: int) -> List[Dict[str, str]]:  # pragma: no cover - interface
        raise NotImplementedError

    async def clear(self, session_id: str) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class InMemoryStore(MemoryStore):
    def __init__(self) -> None:
        self._by_id: Dict[str, Deque[_Turn]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    def _get_lock(self, session_id: str) -> asyncio.Lock:
        # Double-checked pattern with a global lock to create per-session locks
        if session_id in self._locks:
            return self._locks[session_id]
        # Slow path
        async def _ensure() -> asyncio.Lock:
            async with self._global_lock:
                if session_id not in self._locks:
                    self._locks[session_id] = asyncio.Lock()
                return self._locks[session_id]
        # We cannot await here; ensure upfront caller uses _ensure_lock
        # Fallback: return a global lock for early use (rare)
        return self._global_lock

    async def _ensure_lock(self, session_id: str) -> asyncio.Lock:
        async with self._global_lock:
            lock = self._locks.get(session_id)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[session_id] = lock
            return lock

    async def append(self, session_id: str, role: str, content: str) -> None:
        lock = await self._ensure_lock(session_id)
        async with lock:
            existing = self._by_id.get(session_id)
            if existing is None:
                q: Deque[_Turn] = deque()
                self._by_id[session_id] = q
            else:
                q = existing
            q.append(_Turn(role=role, content=content))
            # Trim to max turns (hard cap)
            max_turns = max(0, int(getattr(settings, "MEMORY_MAX_TURNS", 20)))
            if max_turns > 0:
                while len(q) > max_turns:
                    q.popleft()
            # Trim by chars (soft cap): drop from left until under budget
            max_chars = max(0, int(getattr(settings, "MEMORY_MAX_CHARS", 8000)))
            if max_chars > 0:
                def _sum_chars(it: Iterable[_Turn]) -> int:
                    return sum(len(t.content) for t in it)
                while q and _sum_chars(q) > max_chars:
                    q.popleft()

    async def get_window(self, session_id: str, max_chars: int, max_turns: int) -> List[Dict[str, str]]:
        lock = await self._ensure_lock(session_id)
        async with lock:
            q: Optional[Deque[_Turn]] = self._by_id.get(session_id)
            if not q:
                return []
            # Work on a copy to compute window
            items: List[_Turn] = list(q)
        # Compute window outside lock
        items = items[-max_turns:] if max_turns > 0 else items
        # Trim from left by chars
        def _sum_chars_list(lst: List[_Turn]) -> int:
            return sum(len(t.content) for t in lst)
        while items and max_chars > 0 and _sum_chars_list(items) > max_chars:
            items.pop(0)
        return [t.to_message() for t in items]

    async def clear(self, session_id: str) -> None:
        lock = await self._ensure_lock(session_id)
        async with lock:
            self._by_id.pop(session_id, None)


class JsonlStore(MemoryStore):
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._locks: Dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def _ensure_lock(self, session_id: str) -> asyncio.Lock:
        async with self._global_lock:
            lock = self._locks.get(session_id)
            if lock is None:
                lock = asyncio.Lock()
                self._locks[session_id] = lock
            return lock

    def _path(self, session_id: str) -> Path:
        safe = "".join(ch for ch in session_id if ch.isalnum() or ch in ("-", "_"))
        return self.base_dir / f"session_{safe}.jsonl"

    async def append(self, session_id: str, role: str, content: str) -> None:
        lock = await self._ensure_lock(session_id)
        async with lock:
            p = self._path(session_id)
            line = json.dumps({"role": role, "content": content}, ensure_ascii=False)
            with p.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    async def get_window(self, session_id: str, max_chars: int, max_turns: int) -> List[Dict[str, str]]:
        lock = await self._ensure_lock(session_id)
        async with lock:
            p = self._path(session_id)
            if not p.exists():
                return []
            # Read last N lines efficiently
            # Simple approach: read all and slice (sufficient for small budgets); can optimize later.
            try:
                with p.open("r", encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception:
                return []
        # Outside lock: compute window
        turns: List[_Turn] = []
        for line in lines[-max_turns:]:
            try:
                obj = json.loads(line)
                role = str(obj.get("role", "user"))
                content = str(obj.get("content", ""))
                turns.append(_Turn(role=role, content=content))
            except Exception:
                continue
        # Trim by chars
        def _sum_chars_list(lst: List[_Turn]) -> int:
            return sum(len(t.content) for t in lst)
        while turns and max_chars > 0 and _sum_chars_list(turns) > max_chars:
            turns.pop(0)
        return [t.to_message() for t in turns]

    async def clear(self, session_id: str) -> None:
        lock = await self._ensure_lock(session_id)
        async with lock:
            p = self._path(session_id)
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass


_STORE: Optional[MemoryStore] = None


def get_memory_store() -> MemoryStore:
    global _STORE
    if _STORE is not None:
        return _STORE
    try:
        if not getattr(settings, "MEMORY_ENABLED", True):
            _STORE = InMemoryStore()
            return _STORE
        store_kind = getattr(settings, "MEMORY_STORE", "inmemory")
        if store_kind == "jsonl":
            _STORE = JsonlStore(base_dir=getattr(settings, "MEMORY_DIR", Path(".data/memory")))
        else:
            _STORE = InMemoryStore()
        return _STORE
    except Exception:
        _STORE = InMemoryStore()
        return _STORE


async def compose_with_memory(
    messages: List[Mapping[str, str]],
    session_id: Optional[str],
    *,
    max_chars: Optional[int] = None,
    max_turns: Optional[int] = None,
) -> List[Dict[str, str]]:
    """
    Lädt ein Fenster aus der Memory und komponiert es vor die neuen Nachrichten.
    Budgetiert anschließend von links anhand der Zeichenzahl.
    """
    if not session_id or not getattr(settings, "MEMORY_ENABLED", True):
        return [dict(m) for m in messages]
    try:
        store = get_memory_store()
        mc = max_chars if isinstance(max_chars, int) else int(getattr(settings, "MEMORY_MAX_CHARS", 8000))
        mt = max_turns if isinstance(max_turns, int) else int(getattr(settings, "MEMORY_MAX_TURNS", 20))
        window = await store.get_window(session_id, max_chars=mc, max_turns=mt)
        composed: List[Dict[str, str]] = list(window) + [dict(m) for m in messages]
        # Truncation by chars, left side first
        def sum_chars(msgs: List[Mapping[str, str]]) -> int:
            return sum(len(str(m.get("content", ""))) for m in msgs)
        from typing import cast as _cast, Mapping as _Mapping
        while composed and mc > 0 and sum_chars(_cast(List[_Mapping[str, str]], composed)) > mc:
            composed.pop(0)
        return composed
    except Exception:
        return [dict(m) for m in messages]


__all__ = [
    "MemoryStore",
    "InMemoryStore",
    "JsonlStore",
    "get_memory_store",
    "compose_with_memory",
]
