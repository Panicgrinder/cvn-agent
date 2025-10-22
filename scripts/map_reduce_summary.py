#!/usr/bin/env python
"""
Map-Reduce Summarizer für den gesamten Workspace.

Erzeugt pro Datei kompakte Zusammenfassungen (heuristisch, ohne LLM), fasst diese
pro Ordner zusammen und generiert eine finale Gesamtübersicht als Markdown.

Zielordner: app/, scripts/, utils/, tests/, docs/, eval/datasets/
Ausgabe: eval/results/summaries/summary_<timestamp>_<scope>.md

Aufruf:
  python scripts/map_reduce_summary.py [--scopes app,scripts,utils,tests,docs,eval-datasets]
                                      [--max-files 0] [--max-chars 1200]

Hinweis: Dieses Skript nutzt reine statische Heuristiken (AST/Headings/JSON-Struktur),
         damit es ohne Modell/Netzwerk ausführbar ist.
"""
from __future__ import annotations

import os
import sys
import json
import argparse
from utils.time_utils import now_compact
from typing import List, Dict, Any, Tuple, Optional, cast

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT_DIR = os.path.join(PROJECT_ROOT, "eval", "results", "summaries")

SCOPES = {
    "app": os.path.join(PROJECT_ROOT, "app"),
    "scripts": os.path.join(PROJECT_ROOT, "scripts"),
    "utils": os.path.join(PROJECT_ROOT, "utils"),
    "tests": os.path.join(PROJECT_ROOT, "tests"),
    "docs": os.path.join(PROJECT_ROOT, "docs"),
    "eval-datasets": os.path.join(PROJECT_ROOT, "eval", "datasets"),
}

EXCLUDE_DIR_NAMES = {"__pycache__", ".pytest_cache", ".git", ".venv", "venv", "node_modules", "results"}
TEXT_EXTS = {".py", ".md", ".txt", ".json", ".jsonl"}


def _safe_rel(path: str) -> str:
    try:
        return os.path.relpath(path, PROJECT_ROOT)
    except Exception:
        # Fallback für Cross-Drive unter Windows
        p = path.replace("\\", "/")
        root = PROJECT_ROOT.replace("\\", "/")
        return p[len(root)+1:] if p.startswith(root + "/") else p


def is_text_file(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in TEXT_EXTS


def safe_read(path: str, max_bytes: Optional[int] = None) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            if max_bytes is None:
                return f.read()
            else:
                return f.read(max_bytes)
    except Exception:
        return ""


def summarize_python(path: str, text: str, max_chars: int = 1200) -> str:
    import ast
    try:
        tree = ast.parse(text or safe_read(path))
    except Exception:
        # Fallback: Rohtext zusammenkürzen
        return (text or "").strip()[:max_chars]

    mod_doc = ast.get_docstring(tree) or ""
    classes: List[Tuple[str, int]] = []  # (ClassName, method_count)
    functions: List[str] = []
    constants: List[str] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
            classes.append((node.name, method_count))
        elif isinstance(node, ast.FunctionDef):
            functions.append(node.name)
        elif isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    constants.append(t.id)

    lines: List[str] = []
    lines.append(f"Datei: {_safe_rel(path)}")
    if mod_doc:
        d = mod_doc.strip().splitlines()
        head = d[0][:200]
        lines.append(f"Doc: {head}")
    if classes:
        cls_str = ", ".join([f"{n}({m} Methoden)" for n, m in classes[:12]])
        lines.append(f"Klassen: {cls_str}")
    if functions:
        fn_str = ", ".join(functions[:15])
        lines.append(f"Funktionen: {fn_str}")
    if constants:
        c_str = ", ".join(sorted(set(constants))[:12])
        lines.append(f"Konstanten: {c_str}")
    joined = "\n".join(lines)
    return joined[:max_chars]


def summarize_markdown(path: str, text: str, max_chars: int = 1200) -> str:
    lines = text.splitlines()
    headings = [ln.strip() for ln in lines if ln.lstrip().startswith("#")]
    bullets = [ln.strip() for ln in lines if ln.lstrip().startswith(('-', '*'))]
    out: List[str] = [f"Datei: {_safe_rel(path)}"]
    if headings:
        out.append("Überschriften:")
        out.extend([f"- {h}" for h in headings[:12]])
    if bullets:
        out.append(f"Aufzählungen: {min(len(bullets), 50)} Zeilen (Ausschnitt):")
        out.extend([f"  • {b}" for b in bullets[:10]])
    if not headings and not bullets:
        out.append(text[:max_chars])
    return "\n".join(out)[:max_chars]


def summarize_text(path: str, text: str, max_chars: int = 1200) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    head = lines[:15]
    out = [f"Datei: {_safe_rel(path)}", *head]
    return "\n".join(out)[:max_chars]


def summarize_json(path: str, text: str, max_chars: int = 1200) -> str:
    # JSON vs JSONL erkennen
    def jsonl_lines(t: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for i, ln in enumerate(t.splitlines()[:50]):
            ln = ln.strip()
            if not ln:
                continue
            try:
                obj: Any = json.loads(ln)
                if isinstance(obj, dict):
                    out.append(cast(Dict[str, Any], obj))
            except Exception:
                # stop on first non-json line beyond some threshold
                if i > 3:
                    break
                continue
        return out

    content = text.strip()
    is_jsonl = False
    parsed: Any = None
    try:
        parsed = json.loads(content)
    except Exception:
        objs = jsonl_lines(content)
        if objs:
            is_jsonl = True
            parsed = objs

    lines: List[str] = [f"Datei: {_safe_rel(path)}"]
    if parsed is None:
        lines.append("Hinweis: Konnte JSON nicht parsen; Rohtext-Ausschnitt folgt.")
        lines.append(content[:max_chars])
        return "\n".join(lines)

    if is_jsonl and isinstance(parsed, list):
        # Vereine Felder der ersten N Objekte
        key_counts: Dict[str, int] = {}
        lst: List[Any] = cast(List[Any], parsed)
        sample_list: List[Any] = lst[:30]
        for obj in sample_list:
            if isinstance(obj, dict):
                d = cast(Dict[str, Any], obj)
                for k in list(d.keys()):
                    ks: str = str(k)
                    key_counts[ks] = key_counts.get(ks, 0) + 1
        top_keys = sorted(key_counts.items(), key=lambda p: (-p[1], p[0]))[:20]
        lines.append(f"JSONL mit ~{len(lst)} Beispielen (Ausschnitt)")
        lines.append("Felder (häufigste): " + ", ".join(f"{k}({c})" for k, c in top_keys))
    elif isinstance(parsed, list):
        lst2: List[Any] = cast(List[Any], parsed)
        n = len(lst2)
        ex_keys: List[str] = []
        if n:
            first: Any = lst2[0]
            if isinstance(first, dict):
                d0 = cast(Dict[str, Any], first)
                ex_keys = [str(k) for k in list(d0.keys())[:20]]
        lines.append(f"JSON-Array mit {n} Einträgen; Beispiel-Felder: {', '.join(ex_keys)}")
    elif isinstance(parsed, dict):
        dparsed: Dict[str, Any] = cast(Dict[str, Any], parsed)
        keys_list: List[str] = [str(k) for k in list(dparsed.keys())]
        lines.append(f"JSON-Objekt; Top-Level-Felder: {', '.join(keys_list[:25])}")
    else:
        lines.append("JSON-Inhalt erkannt (vereinfachte Struktur)")
    return "\n".join(lines)[:max_chars]


def summarize_file(path: str, max_chars: int = 1200) -> str:
    _, ext = os.path.splitext(path)
    text = safe_read(path, max_bytes=512*1024)  # large cap but safe
    ext = ext.lower()
    if ext == ".py":
        return summarize_python(path, text, max_chars)
    if ext == ".md":
        return summarize_markdown(path, text, max_chars)
    if ext in {".json", ".jsonl"}:
        return summarize_json(path, text, max_chars)
    return summarize_text(path, text, max_chars)


def walk_scope(scope_dir: str, max_files: int = 0) -> List[str]:
    summaries: List[str] = []
    count = 0
    for root, dirnames, filenames in os.walk(scope_dir):
        # exclude noisy dirs
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIR_NAMES]
        for fn in sorted(filenames):
            fp = os.path.join(root, fn)
            if not is_text_file(fp):
                continue
            try:
                s = summarize_file(fp)
                summaries.append(s)
                count += 1
                if max_files and count >= max_files:
                    return summaries
            except Exception:
                continue
    return summaries


def write_md(out_path: str, title: str, sections: List[Tuple[str, List[str]]]) -> None:
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        for heading, paras in sections:
            f.write(f"## {heading}\n\n")
            for p in paras:
                f.write(p)
                f.write("\n\n")


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scopes", type=str, default=",".join(SCOPES.keys()), help="Komma-separierte Scopes")
    ap.add_argument("--max-files", type=int, default=0, help="Max. Dateien pro Scope (0=alle)")
    ap.add_argument("--max-chars", type=int, default=1200, help="Max. Zeichen pro Dateizusammenfassung")
    ap.add_argument("--out-dir", type=str, default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)

    timestamp = now_compact()
    scopes = [s.strip() for s in args.scopes.split(",") if s.strip()]

    scope_files: List[str] = []
    merged_sections: List[Tuple[str, List[str]]] = []

    for scope in scopes:
        scope_dir = SCOPES.get(scope)
        if not scope_dir or not os.path.isdir(scope_dir):
            continue
        summaries = walk_scope(scope_dir, max_files=args.max_files)
        if not summaries:
            continue
        out_path = os.path.join(args.out_dir, f"summary_{timestamp}_{scope}.md")
        write_md(out_path, f"Workspace Zusammenfassung – {scope}", [("Dateien", summaries)])
        scope_files.append(out_path)
        # Für Merge bereitstellen (gekürzt pro Scope)
        merged_sections.append((scope, summaries[: min(50, len(summaries))]))

    # Merge-Datei
    if scope_files:
        merged_path = os.path.join(args.out_dir, f"summary_ALL_{timestamp}.md")
        write_md(merged_path, "Workspace Zusammenfassung – Gesamt", merged_sections)
        print(json.dumps({
            "timestamp": timestamp,
            "out_dir": args.out_dir,
            "scopes": scopes,
            "files": scope_files,
            "merged": merged_path,
        }, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"error": "Keine Scopes gefunden oder keine Dateien"}, ensure_ascii=False))
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
