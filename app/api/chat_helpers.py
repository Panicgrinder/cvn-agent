"""
Hilfsfunktionen für den Chat-Endpunkt.
"""

import functools
from typing import Any, Dict, List, Optional, Tuple, cast

from .models import ChatMessage
from app.core.prompts import DEFAULT_SYSTEM_PROMPT
from app.core.settings import settings


@functools.lru_cache(maxsize=1)
def get_system_prompt() -> str:
    """
    Liefert den zentral definierten System-Prompt aus app.core.prompts.
    Der Prompt wird gecached, um wiederholte Zugriffe zu vermeiden.
    """
    return DEFAULT_SYSTEM_PROMPT.strip()


def ensure_system_message(messages: List[ChatMessage]) -> List[ChatMessage]:
    """
    Stellt sicher, dass die Nachrichtenliste einen System-Turn enthält.
    Wenn kein System-Turn vorhanden ist, wird einer am Anfang eingefügt.
    
    Args:
        messages: Liste von ChatMessage-Objekten
        
    Returns:
        Liste von ChatMessage-Objekten mit garantiertem System-Turn
    """
    # Prüfe, ob bereits ein System-Turn vorhanden ist
    has_system = any(msg.role == "system" for msg in messages)
    
    if not has_system:
        # Füge System-Turn am Anfang ein
        system_content = get_system_prompt()
        system_message = ChatMessage(role="system", content=system_content)
        return [system_message] + messages
    
    return messages


def _coerce_float(val: Any) -> Optional[float]:
    try:
        return float(val)
    except Exception:
        return None


def _coerce_int(val: Any) -> Optional[int]:
    try:
        iv = int(val)
        return iv
    except Exception:
        return None


def _coerce_str_list(val: Any) -> Optional[List[str]]:
    if isinstance(val, list):
        out: List[str] = []
        # Elemente explizit als Any behandeln, damit str() typklar ist
        for x in cast(List[Any], val):
            try:
                out.append(str(x))
            except Exception:
                continue
        return out
    if isinstance(val, str):
        # Einzelnes Stop-Token als Liste interpretieren
        return [val]
    return None


def normalize_ollama_options(
    raw_options: Dict[str, Any] | None,
    *,
    eval_mode: bool = False,
) -> Tuple[Dict[str, Any], str]:
    """
    Normalisiert Request-Options zu einem kompakten Options-Dict für Ollama
    und gibt zusätzlich den Host zurück.

    Regeln:
    - temperature: float; im eval_mode auf <= 0.25 gedeckelt
    - num_predict: aus num_predict oder max_tokens; 1..REQUEST_MAX_TOKENS
    - top_p: float; ignorieren, wenn nicht parsebar
    - host: string, Default aus settings
    - Erweiterte Felder (wenn parsebar):
        num_ctx (int), repeat_penalty (float), presence_penalty (float),
        frequency_penalty (float), seed (int), repeat_last_n (int), stop (List[str])
    """
    ro: Dict[str, Any] = dict(raw_options or {})
    out: Dict[str, Any] = {}

    # temperature
    temp = _coerce_float(ro.get("temperature", settings.TEMPERATURE))
    if temp is None:
        temp = settings.TEMPERATURE
    if eval_mode:
        temp = min(temp, 0.25)
    out["temperature"] = float(temp)

    # num_predict / max_tokens
    max_req = settings.REQUEST_MAX_TOKENS
    np_raw = ro.get("num_predict", ro.get("max_tokens", max_req))
    np_val = _coerce_int(np_raw)
    if np_val is None:
        np_val = max_req
    np_val = max(1, min(int(np_val), max_req))
    out["num_predict"] = int(np_val)

    # top_p (optional)
    top_p = _coerce_float(ro.get("top_p"))
    if top_p is not None:
        out["top_p"] = float(top_p)

    # Erweiterte Felder (optional, nur wenn parsebar)
    num_ctx = _coerce_int(ro.get("num_ctx"))
    if isinstance(num_ctx, int) and num_ctx > 0:
        out["num_ctx"] = int(num_ctx)

    repeat_penalty = _coerce_float(ro.get("repeat_penalty"))
    if repeat_penalty is not None:
        out["repeat_penalty"] = float(repeat_penalty)

    presence_penalty = _coerce_float(ro.get("presence_penalty"))
    if presence_penalty is not None:
        out["presence_penalty"] = float(presence_penalty)

    frequency_penalty = _coerce_float(ro.get("frequency_penalty"))
    if frequency_penalty is not None:
        out["frequency_penalty"] = float(frequency_penalty)

    seed = _coerce_int(ro.get("seed"))
    if seed is not None:
        out["seed"] = int(seed)

    repeat_last_n = _coerce_int(ro.get("repeat_last_n"))
    if repeat_last_n is not None and repeat_last_n >= 0:
        out["repeat_last_n"] = int(repeat_last_n)

    stop = _coerce_str_list(ro.get("stop"))
    if stop:
        out["stop"] = stop

    # Host
    host = str(ro.get("host", settings.OLLAMA_HOST))
    return out, host


__all__ = [
    "get_system_prompt",
    "ensure_system_message",
    "normalize_ollama_options",
]