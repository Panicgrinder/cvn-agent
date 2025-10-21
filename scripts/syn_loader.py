from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger("syn_loader")

ALLOWED_CHARS = set("abcdefghijklmnopqrstuvwxyz0123456789 äöüß./-_")


def _merge_dicts(base: Dict[str, List[str]], overlay: Dict[str, List[str]]) -> Dict[str, List[str]]:
    out = dict(base)
    for k, v in overlay.items():
        out[k] = list(v)
    return out


def _sanitize_dict(d: Dict[str, List[str]]) -> Tuple[Dict[str, List[str]], int]:
    dropped = 0
    out: Dict[str, List[str]] = {}
    for k, vals in d.items():
        if not isinstance(k, str):
            dropped += 1
            continue
        key = "".join(ch for ch in k.lower() if ch in ALLOWED_CHARS).strip()
        if not key:
            dropped += 1
            continue
        norm_vals: List[str] = []
        for val in vals:
            if not isinstance(val, str):
                dropped += 1
                continue
            nv = "".join(ch for ch in val.lower() if ch in ALLOWED_CHARS).strip()
            if nv:
                norm_vals.append(nv)
            else:
                dropped += 1
        # dedupe + sort
        norm_vals = sorted(list({*norm_vals}))
        out[key] = norm_vals
    return out, dropped


def load_synonyms() -> Tuple[Dict[str, List[str]], int]:
    """Load and merge synonyms from eval/config/, with additional and local overlays.
    Returns (merged_dict, count_total).
    """
    base = Path("eval/config/synonyms.json")
    add = Path("eval/config/synonyms.additional.json")
    local = Path("eval/config/synonyms.local.json")

    def _read(p: Path) -> Dict[str, List[str]]:
        try:
            if p.exists():
                with p.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return {str(k): list(v) for k, v in data.items() if isinstance(v, list)}
        except Exception as e:
            logger.warning(f"Fehler beim Laden von {p}: {e}")
        return {}

    b = _read(base)
    a = _read(add)
    l = _read(local)

    merged = _merge_dicts(b, a)
    merged = _merge_dicts(merged, l)

    sanitized, dropped = _sanitize_dict(merged)

    # logging
    info_prefix = "JSON" if (os.environ.get("LOG_JSON", "").lower() in ("1", "true", "yes")) else "TEXT"
    logger.info("Ladevorgang Synonyme gestartet")
    logger.info(f"Anzahl der Synonym-Einträge (merged): {len(sanitized)}; dropped={dropped}")

    return sanitized, len(sanitized)
