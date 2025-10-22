import json
from pathlib import Path
from typing import List, Optional, Iterable

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

ALLOWED_EXTS = {".md", ".txt", ".json", ".jsonl", ".ref"}


def _iter_paths(paths: List[str]) -> Iterable[Path]:
    """Erweitert gemischte Eingaben (Dateien/Verzeichnisse) in eine geordnete Dateiliste.

    - Unterstützt Verzeichnisse: nimmt Dateien mit ALLOWED_EXTS (nicht rekursiv) auf
    - .ref Dateien: werden im Loader speziell behandelt (verweisen auf andere Dateien)
    - Reihenfolge: wie angegeben; für Verzeichnisse alphabetisch nach Dateiname
    """
    for p in paths:
        pp = Path(p)
        if not pp.exists():
            continue
        if pp.is_dir():
            # Nur erste Ebene, alphabetisch
            for child in sorted(pp.iterdir(), key=lambda x: x.name.lower()):
                if child.is_file() and child.suffix.lower() in ALLOWED_EXTS:
                    yield child
        elif pp.is_file():
            yield pp


def _resolve_ref(path: Path) -> Optional[Path]:
    """Liest eine .ref Datei: erste nicht-leere Zeile ist ein (relativer oder absoluter) Dateipfad."""
    try:
        content = path.read_text(encoding="utf-8")
        for line in content.splitlines():
            s = line.strip()
            if not s:
                continue
            target = Path(s)
            if not target.is_absolute():
                # Relativ zum Repo-Root (aktuelles Arbeitsverzeichnis)
                target = Path.cwd() / target
            return target if target.exists() and target.is_file() else None
    except Exception:
        return None
    return None


def load_context_notes(paths: List[str], max_chars: int = 4000) -> Optional[str]:
    """
    Lädt lokale Kontext-Notizen aus Dateien und/oder Verzeichnissen.
    Unterstützte Formate: .md/.txt (Text), .json, .jsonl; zusätzlich .ref als Verweisdatei.

    Verhalten:
    - Jeder Eintrag in `paths` kann Datei oder Verzeichnis sein.
    - Verzeichnisse: Es werden alle Dateien mit erlaubten Endungen (nicht rekursiv) geladen.
    - .ref-Datei: enthält Pfad zu einer Zieldatei (erste nicht-leere Zeile), die geladen wird.
    - Rückgabe: zusammengeführter Text (mit \n\n separiert), auf max_chars gekürzt.
    """
    chunks: List[str] = []
    for path_obj in _iter_paths(paths):
        try:
            lower = path_obj.suffix.lower()
            target = path_obj
            if lower == ".ref":
                ref = _resolve_ref(path_obj)
                if ref is None:
                    continue
                target = ref
                lower = target.suffix.lower()

            if lower == ".jsonl":
                txt = _read_jsonl(str(target))
            elif lower == ".json":
                txt = _read_json(str(target))
            else:
                # .md, .txt, Sonstiges als Text
                txt = _read_text(str(target))

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
