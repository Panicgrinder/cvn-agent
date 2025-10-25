from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Tuple

try:
    from app.core.settings import settings
except Exception:  # pragma: no cover - during type analysis
    settings = None  # type: ignore[assignment]

# Tool type: accepts args dict, returns result dict
ToolFunc = Callable[[Dict[str, Any]], Dict[str, Any]]

_REGISTRY: Dict[str, ToolFunc] = {}


def register_tool(name: str, func: ToolFunc) -> None:
    """Register a tool function under a unique name (idempotent)."""
    if not isinstance(name, str) or not name:
        raise ValueError("tool name must be non-empty string")
    _REGISTRY[name] = func


def list_tools() -> Tuple[str, ...]:
    return tuple(sorted(_REGISTRY.keys()))


def is_allowed(name: str) -> bool:
    """Check whitelist from settings: when disabled, deny; when list empty but enabled, allow none unless explicitly whitelisted."""
    if settings is None:
        return False
    if not getattr(settings, "TOOLS_ENABLED", False):
        return False
    wl = getattr(settings, "TOOLS_WHITELIST", [])
    if isinstance(wl, (list, tuple)):
        return name in wl
    return False


def call_tool(name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Call a registered tool if allowed by whitelist.

    Returns a structured dict with either {ok: true, data: {...}} or {ok: false, error: "..."}.
    """
    if name not in _REGISTRY:
        return {"ok": False, "error": f"unknown tool: {name}"}
    if not is_allowed(name):
        return {"ok": False, "error": f"tool not allowed: {name}"}
    func = _REGISTRY[name]
    try:
        res = func(dict(args or {}))
        if not isinstance(res, dict):
            return {"ok": False, "error": "tool returned non-dict"}
        return {"ok": True, "data": res}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


# ------------------- Built-in minimal tool(s) -------------------

def _calc_add(args: Dict[str, Any]) -> Dict[str, Any]:
    """Add two numeric values: {a: number, b: number} -> {result}.
    Coerces via float(); returns result as float.
    """
    a = float(args.get("a", 0))
    b = float(args.get("b", 0))
    return {"result": float(a + b)}


# Register minimal example
register_tool("calc_add", _calc_add)

__all__ = [
    "register_tool",
    "list_tools",
    "call_tool",
    "is_allowed",
]
