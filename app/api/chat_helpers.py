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


def _coerce_bool(val: Any) -> Optional[bool]:
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    if isinstance(val, str):
        s = val.strip().lower()
        if s in {"1", "true", "yes", "y", "on"}:
            return True
        if s in {"0", "false", "no", "n", "off"}:
            return False
    return None


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


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

    # top_p (Default aus Settings, Range 0..1)
    top_p = _coerce_float(ro.get("top_p", settings.TOP_P))
    if top_p is not None:
        out["top_p"] = float(_clamp01(top_p))

    # top_k (Default aus Settings, >0)
    top_k = _coerce_int(ro.get("top_k", settings.TOP_K))
    if top_k is not None and top_k > 0:
        out["top_k"] = int(top_k)

    # Erweiterte Felder (optional, nur wenn parsebar)
    num_ctx = _coerce_int(ro.get("num_ctx", settings.NUM_CTX_DEFAULT))
    if isinstance(num_ctx, int) and num_ctx > 0:
        out["num_ctx"] = int(num_ctx)

    repeat_penalty = _coerce_float(ro.get("repeat_penalty", settings.REPEAT_PENALTY))
    if repeat_penalty is not None:
        out["repeat_penalty"] = float(repeat_penalty)

    presence_penalty = _coerce_float(ro.get("presence_penalty", 0.0))
    if presence_penalty is not None:
        out["presence_penalty"] = float(presence_penalty)

    frequency_penalty = _coerce_float(ro.get("frequency_penalty", 0.0))
    if frequency_penalty is not None:
        out["frequency_penalty"] = float(frequency_penalty)

    seed = _coerce_int(ro.get("seed"))
    if seed is not None:
        out["seed"] = int(seed)

    repeat_last_n = _coerce_int(ro.get("repeat_last_n", settings.REPEAT_LAST_N))
    if repeat_last_n is not None and repeat_last_n >= 0:
        out["repeat_last_n"] = int(repeat_last_n)

    stop = _coerce_str_list(ro.get("stop"))
    if stop:
        out["stop"] = stop

    # min_p / typical_p / tfs_z (0..1)
    min_p = _coerce_float(ro.get("min_p", settings.MIN_P))
    if min_p is not None:
        out["min_p"] = float(_clamp01(min_p))

    typical_p = _coerce_float(ro.get("typical_p", settings.TYPICAL_P))
    if typical_p is not None:
        out["typical_p"] = float(_clamp01(typical_p))

    tfs_z = _coerce_float(ro.get("tfs_z", settings.TFS_Z))
    if tfs_z is not None:
        out["tfs_z"] = float(_clamp01(tfs_z))

    # Mirostat (0,1,2) + Parameter
    mirostat = _coerce_int(ro.get("mirostat", settings.MIROSTAT))
    if mirostat is not None:
        ms = 0 if mirostat < 0 else (2 if mirostat > 2 else mirostat)
        out["mirostat"] = int(ms)
    mirostat_tau = _coerce_float(ro.get("mirostat_tau", settings.MIROSTAT_TAU))
    if mirostat_tau is not None:
        out["mirostat_tau"] = float(mirostat_tau)
    mirostat_eta = _coerce_float(ro.get("mirostat_eta", settings.MIROSTAT_ETA))
    if mirostat_eta is not None:
        out["mirostat_eta"] = float(mirostat_eta)

    # penalize_newline (bool)
    penalize_newline = _coerce_bool(ro.get("penalize_newline", settings.PENALIZE_NEWLINE))
    if penalize_newline is not None:
        out["penalize_newline"] = bool(penalize_newline)

    # Host
    host = str(ro.get("host", settings.OLLAMA_HOST))
    return out, host


__all__ = [
    "get_system_prompt",
    "ensure_system_message",
    "normalize_ollama_options",
]