from __future__ import annotations
import os, json, hashlib, threading
from typing import Any, Dict, Optional

def make_key(obj: Any) -> str:
    try:
        payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except Exception:
        payload = repr(obj)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

class EvalCache:
    """
    Sehr einfacher JSONL-Cache:
    - Datei mit Zeilen {"k": <hash>, "v": <value>}
    - In-Memory-Index (dict) + append-on-write
    """
    def __init__(self, path: str) -> None:
        self.path = path
        self._idx: Dict[str, Any] = {}
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            rec = json.loads(line)
                            k = rec.get("k")
                            if k is not None and "v" in rec:
                                self._idx[str(k)] = rec["v"]
                        except Exception:
                            continue
            except Exception:
                # defekte Cache-Datei wird ignoriert
                pass

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            return self._idx.get(key)

    def put(self, key: str, value: Any) -> None:
        rec: Dict[str, Any] = {"k": key, "v": value}
        data = json.dumps(rec, ensure_ascii=False)
        with self._lock:
            self._idx[key] = value
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(data + "\n")