"""
Einfache, optionale In-Memory Sitzungsverwaltung.

Zweck:
- Nachrichtenkontext pro session_id puffern (klein, flüchtig)
- Begrenzen nach Anzahl Nachrichten und Gesamtlänge

Hinweis:
- Nicht persistent; für Production ggf. Redis o.ä. nutzen.
"""
from __future__ import annotations

from typing import Dict, List, Mapping
from threading import RLock


class SessionMemory:
    def __init__(self) -> None:
        self._by_id: Dict[str, List[Mapping[str, str]]] = {}
        self._lock = RLock()

    def get(self, session_id: str) -> List[Mapping[str, str]]:
        with self._lock:
            return list(self._by_id.get(session_id, []))

    def put_and_trim(
        self,
        session_id: str,
        messages: List[Mapping[str, str]],
        max_messages: int,
        max_chars: int,
    ) -> List[Mapping[str, str]]:
        """
        Fügt Nachrichten an und trimmt nach Anzahl und Zeichen.
        Gibt den aktuellen, getrimmten Verlauf zurück.
        """
        with self._lock:
            cur = self._by_id.get(session_id, [])
            cur.extend(messages)
            # Trim nach Anzahl
            if max_messages > 0 and len(cur) > max_messages:
                cur = cur[-max_messages:]
            # Trim nach Zeichen
            if max_chars > 0:
                def total_chars(seq: List[Mapping[str, str]]) -> int:
                    return sum(len(str(m.get("content", ""))) for m in seq)
                while cur and total_chars(cur) > max_chars:
                    cur.pop(0)
            self._by_id[session_id] = cur
            return list(cur)


# Singleton-ähnliche, einfache Instanz
session_memory = SessionMemory()

__all__ = ["SessionMemory", "session_memory"]
