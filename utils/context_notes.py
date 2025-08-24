import os
import json
from typing import List, Optional

def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def _read_json(path: str) -> str:
    data = None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Normalisiere in eine kompakte, menschenlesbare Textform
    if isinstance(data, dict):
        # Schlüssel alphabetisch, zwecks Stabilität
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    if isinstance(data, list):
        return json.dumps(data, ensure_ascii=False, indent=2)
    return str(data)

def _read_jsonl(path: str) -> str:
    lines: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
                lines.append(json.dumps(obj, ensure_ascii=False))
            except Exception:
                # Fallback: Rohzeile
                lines.append(s)
    return "\n".join(lines)

def load_context_notes(paths: List[str], max_chars: int = 4000) -> Optional[str]:
    """
    Lädt lokale Kontext-Notizen aus der ersten existierenden Datei in `paths`.
    Unterstützte Formate: .md/.txt (Text), .json, .jsonl
    Gibt den zusammengeführten Text (bei mehreren existierenden Pfaden) bis zu max_chars zurück.
    """
    chunks: List[str] = []
    for p in paths:
        if not os.path.exists(p):
            continue
        try:
            lower = p.lower()
            if lower.endswith(".jsonl"):
                txt = _read_jsonl(p)
            elif lower.endswith(".json"):
                txt = _read_json(p)
            else:
                # .md, .txt, Sonstiges als Text
                txt = _read_text(p)
            if txt:
                chunks.append(txt.strip())
        except Exception:
            # still übergehen, damit ein defekter Pfad die App nicht stoppt
            continue

    if not chunks:
        return None
    merged = "\n\n".join(chunks)
    if len(merged) > max_chars:
        return merged[: max_chars - 3] + "..."
    return merged
