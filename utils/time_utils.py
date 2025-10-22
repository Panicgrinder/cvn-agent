"""Zentrale Zeit-Helfer für konsistente Zeitstempel.

Alle Funktionen nutzen standardmäßig die lokale Zeitzone des Systems und
liefern "aware"-Zeitstempel mit Offset, sofern möglich.
Optional kann per Umgebungsvariable "CVN_TZ" (oder POSIX "TZ") eine
Zeitzone gesetzt werden (z. B. "Europe/Berlin").

Formate:
- now_human(): "YYYY-MM-DD HH:MM" (für DONELOG)
- now_human_tz(): wie oben, plus TZ-Abkürzung oder UTC-Offset (z. B. "CET" oder "UTC+01:00")
- now_compact(): "YYYYMMDD_%H%M" (für Dateinamen/Reports)
- now_iso(): ISO-8601 mit Offset (Sekundenauflösung)
"""
from __future__ import annotations

from datetime import datetime, tzinfo
import os
from typing import Optional

try:
    # Python 3.9+: zoneinfo aus der stdlib
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover - Fallback für sehr alte Umgebungen
    ZoneInfo = None  # type: ignore


def _get_tz() -> Optional[tzinfo]:
    tz_name = os.getenv("CVN_TZ") or os.getenv("TZ")
    if tz_name and ZoneInfo is not None:
        try:
            return ZoneInfo(tz_name)
        except Exception:
            return None
    return None


def now_aware() -> datetime:
    tz = _get_tz()
    if tz is not None:
        return datetime.now(tz=tz)
    # Fallback: Systemlokalzeit mit Offset (aware)
    return datetime.now().astimezone()


def now_human() -> str:
    return now_aware().strftime("%Y-%m-%d %H:%M")


def now_compact() -> str:
    return now_aware().strftime("%Y%m%d_%H%M")


def now_iso() -> str:
    dt = now_aware()
    # Sekundenauflösung, inkl. Offset wenn vorhanden
    try:
        return dt.isoformat(timespec="seconds")
    except TypeError:  # Python < 3.11 ohne timespec
        return dt.isoformat()


def _format_utc_offset(dt: datetime) -> str:
    off = dt.utcoffset()
    if off is None:
        return ""
    total_seconds = int(off.total_seconds())
    sign = "+" if total_seconds >= 0 else "-"
    total_seconds = abs(total_seconds)
    hours, rem = divmod(total_seconds, 3600)
    minutes = rem // 60
    return f"UTC{sign}{hours:02d}:{minutes:02d}"


def tz_label() -> str:
    """Liefert eine kompakte TZ-Bezeichnung: Abkürzung oder UTC±HH:MM."""
    dt = now_aware()
    name = dt.tzname()
    if name:
        return name
    return _format_utc_offset(dt) or "UTC"


def now_human_tz() -> str:
    dt = now_aware()
    label = dt.tzname() or _format_utc_offset(dt) or "UTC"
    return f"{dt.strftime('%Y-%m-%d %H:%M')} {label}"
