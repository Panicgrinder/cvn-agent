import os
import json
import platform
from typing import List

from app.core.settings import settings


def ensure_file(path: str) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        # Versuch: aus Sample kopieren, wenn vorhanden
        sample_md = os.path.join(os.path.dirname(path), "context.local.sample.md")
        try:
            if os.path.exists(sample_md):
                with open(sample_md, "r", encoding="utf-8") as f_in, open(path, "w", encoding="utf-8") as f_out:
                    f_out.write(f_in.read())
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("# Kontext-Notizen\n\n")
        except Exception:
            with open(path, "w", encoding="utf-8") as f:
                f.write("# Kontext-Notizen\n\n")
    return path


def pick_target(paths: List[str]) -> str:
    # Nimm den ersten existierenden, sonst den ersten konfigurierten
    for p in paths:
        if os.path.exists(p):
            return p
    return paths[0] if paths else os.path.join("eval", "config", "context.local.md")


def open_file(path: str) -> None:
    system = platform.system().lower()
    if system.startswith("win"):
        os.startfile(path)
    elif system == "darwin":
        os.system(f"open '{path}'")
    else:
        os.system(f"xdg-open '{path}' 2>/dev/null || sensible-editor '{path}' || nano '{path}'")


def main() -> int:
    paths = getattr(settings, "CONTEXT_NOTES_PATHS", [os.path.join("eval", "config", "context.local.md")])
    target = pick_target(paths)
    target = ensure_file(target)
    print(json.dumps({"opening": target}))
    try:
        open_file(target)
    except Exception as e:
        print(json.dumps({"error": str(e), "path": target}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
