from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Literal

Mode = Literal["rpg", "general"]


def detect_requested_mode_from_messages(messages: List[Dict[str, Any]]) -> Optional[Mode]:
    """Heuristik: erkennt gewünschten Modus anhand der User‑Nachrichten.

    - RPG: Schlüsselwörter/Formatindikatoren (novapolis, chronistin, /roll, szene:, konsequenz:, optionen:)
    - General: neutrale Hinweise (neutral, sachlich, ohne rpg, kein rpg, allgemein, keine persona)
    """
    if not messages:
        return None
    text = " ".join(str(m.get("content", "")) for m in messages if str(m.get("role", "")).lower() == "user").lower()
    if any(k in text for k in ["novapolis", "chronistin", "/roll", "szene:", "konsequenz:", "optionen:"]):
        return "rpg"
    if any(k in text for k in ["neutral", "sachlich", "ohne rpg", "kein rpg", "allgemein", "keine persona"]):
        return "general"
    return None


class SessionModeStore:
    """Prozesslokaler, einfacher Session→Mode Speicher mit TTL und Kapazitätslimit."""

    def __init__(self, ttl_minutes: int, max_entries: int):
        self._ttl = max(1, int(ttl_minutes)) * 60
        self._max = max(100, int(max_entries))
        self._store: Dict[str, Tuple[Mode, float]] = {}
        self._lock = threading.Lock()

    def get(self, sid: Optional[str]) -> Optional[Mode]:
        if not sid:
            return None
        now = time.time()
        with self._lock:
            ent = self._store.get(sid)
            if not ent:
                return None
            mode, ts = ent
            if now - ts > self._ttl:
                self._store.pop(sid, None)
                return None
            return mode

    def set(self, sid: Optional[str], mode: Mode) -> None:
        if not sid:
            return
        now = time.time()
        with self._lock:
            if len(self._store) >= self._max:
                # FIFO/LRU-ähnlicher einfacher Abwurf: ältesten Eintrag entfernen
                oldest_key = min(self._store.items(), key=lambda kv: kv[1][1])[0]
                self._store.pop(oldest_key, None)
            self._store[sid] = (mode, now)


# Singleton-Store Konfiguration aus Settings ableiten (fail‑open Defaults)
try:
    from app.core.settings import settings as _settings
    _ttl = getattr(_settings, "AUTO_MODE_MEMORY_TTL_MIN", 120)
    _max = getattr(_settings, "AUTO_MODE_MEMORY_MAX", 1000)
except Exception:
    _ttl, _max = 120, 1000

SESSION_MODES = SessionModeStore(ttl_minutes=_ttl, max_entries=_max)


def resolve_mode(
    *,
    session_id: Optional[str],
    eval_mode: bool,
    unrestricted_mode: bool,
    messages: List[Dict[str, Any]],
    default_mode: Mode,
    persist: bool = True,
) -> Mode:
    """Bestimmt den Antwortmodus nach Priorität (hoch → niedrig):

    1) Flags: unrestricted_mode → rpg; eval_mode → general
    2) Heuristik aus User‑Nachrichten
    3) Gemerkter Sitzungsmodus (SESSION_MODES)
    4) Default (AUTO_MODE_DEFAULT)
    """
    if unrestricted_mode:
        mode: Mode = "rpg"
    elif eval_mode:
        mode = "general"
    else:
        m = detect_requested_mode_from_messages(messages)
        if m is not None:
            mode = m
        else:
            remembered = SESSION_MODES.get(session_id)
            mode = remembered if remembered else default_mode

    if persist and session_id:
        SESSION_MODES.set(session_id, mode)
    return mode


__all__ = [
    "Mode",
    "detect_requested_mode_from_messages",
    "SessionModeStore",
    "SESSION_MODES",
    "resolve_mode",
]
