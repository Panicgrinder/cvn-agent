#!/usr/bin/env python
import os, sys, json
from typing import Dict, Set, Protocol

class _EncoderLike(Protocol):
    def encode(self, text: str) -> list[int]: ...

TRY_TIKTOKEN = True
enc: _EncoderLike | None = None
if TRY_TIKTOKEN:
    try:
        import importlib
        tiktoken = importlib.import_module("tiktoken")  # dynamic import
        enc = tiktoken.get_encoding("cl100k_base")
    except Exception:
        enc = None

EXCLUDE_DIRS: Set[str] = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "eval/results"}
TEXT_EXTS: Set[str] = {".py", ".md", ".json", ".jsonl", ".txt", ".gitignore", ".cfg", ".ini", ".yml", ".yaml"}

def is_text_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in TEXT_EXTS

def count_tokens(text: str) -> int:
    if enc is not None:
        try:
            return len(enc.encode(text))
        except Exception:
            pass
    # Fallback-Heuristik
    return max(1, int(len(text) / 4))

def main() -> int:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    total_tokens = 0
    per_dir: Dict[str, int] = {}
    files_counted = 0

    for dirpath, dirnames, filenames in os.walk(root):
        # ausschließen
        rel = os.path.relpath(dirpath, root).replace("\\", "/")
        dirnames[:] = [d for d in dirnames if os.path.join(rel, d).strip("./") not in EXCLUDE_DIRS and d not in EXCLUDE_DIRS]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            relfp = os.path.relpath(fp, root).replace("\\", "/")
            if any(part in EXCLUDE_DIRS for part in relfp.split("/")):
                continue
            if not is_text_file(fp):
                continue
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                tok = count_tokens(text)
                total_tokens += tok
                top = relfp.split("/")[0]
                per_dir[top] = per_dir.get(top, 0) + tok
                files_counted += 1
            except Exception:
                continue

    print(json.dumps({
        "files": files_counted,
        "total_tokens_estimate": total_tokens,
        "by_top_level_dir": per_dir,
        "note": "Heuristik ~4 Bytes/Token, exkl. eval/results & Caches"
    }, ensure_ascii=False, indent=2))
    # simple Daumenregel
    mb = (total_tokens * 4) / (1024*1024)
    print(f"\nApprox. Größe ~ {mb:.2f} MB Text, Tokens ~ {total_tokens:,}")
    print("Richtwert: <=100k Tokens: One‑Shot möglich; 100k–200k: grenzwertig; >200k: chunken/map‑reduce.")
    return 0

if __name__ == "__main__":
    sys.exit(main())