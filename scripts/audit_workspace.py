#!/usr/bin/env python
"""
Audit: Ermittelt potenziell ungenutzte Dateien für API (app) und Evaluierung (scripts/run_eval).
Ergebnisse sind heuristisch und dienen als Startpunkt für Aufräumarbeiten.

Ausführung:
  python scripts/audit_workspace.py
"""
import os
import sys
import ast
from typing import Dict, Set, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIRS = ["app", "scripts", "utils", "eval", "docs", "examples"]
ENTRYPOINTS = [
    ("app.main", os.path.join(PROJECT_ROOT, "app", "main.py")),
    ("scripts.run_eval", os.path.join(PROJECT_ROOT, "scripts", "run_eval.py")),
]


def to_module_name(path: str) -> str:
    try:
        rel = os.path.relpath(path, PROJECT_ROOT).replace(os.sep, "/")
    except Exception:
        # Fallback: nutze absolute Pfadangabe und schneide Projektwurzel grob weg
        p = path.replace("\\", "/")
        root = PROJECT_ROOT.replace("\\", "/")
        rel = p[len(root)+1:] if p.startswith(root + "/") else os.path.basename(p)
    if rel.endswith("/__init__.py"):
        rel = rel[: -len("/__init__.py")]
    elif rel.endswith(".py"):
        rel = rel[: -3]
    return rel.replace("/", ".")


def discover_pyfiles() -> Dict[str, str]:
    files: Dict[str, str] = {}
    for base in SRC_DIRS:
        base_path = os.path.join(PROJECT_ROOT, base)
        if not os.path.isdir(base_path):
            continue
        for root, _, filenames in os.walk(base_path):
            for fn in filenames:
                if fn.endswith(".py"):
                    fp = os.path.join(root, fn)
                    files[to_module_name(fp)] = fp
    return files


def parse_imports(py_path: str) -> Set[str]:
    deps: Set[str] = set()
    try:
        with open(py_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=py_path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    deps.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.level == 0 and node.module:
                    deps.add(node.module)
    except Exception:
        pass
    return deps


def build_graph(pyfiles: Dict[str, str]) -> Dict[str, Set[str]]:
    graph: Dict[str, Set[str]] = {m: set() for m in pyfiles}
    mod_set = set(pyfiles.keys())
    for mod, path in pyfiles.items():
        imports = parse_imports(path)
        # Fuzzy-Zuordnung: jede importierte Kette mapt auf alle bekannten Module mit gleichem Prefix
        for imp in imports:
            for other in mod_set:
                if other == imp or other.startswith(imp + ".") or imp.startswith(other + "."):
                    graph[mod].add(other)
    return graph


def reachable_from(entry_modules: List[str], graph: Dict[str, Set[str]]) -> Set[str]:
    seen: Set[str] = set()
    stack: List[str] = []
    mod_set = set(graph.keys())
    # Seed: alle Module, die exakt oder als Suffix mit Entry übereinstimmen
    for em in entry_modules:
        for m in mod_set:
            if m == em or m.endswith("." + em) or em.endswith("." + m):
                stack.append(m)
    while stack:
        m = stack.pop()
        if m in seen:
            continue
        seen.add(m)
        for dep in graph.get(m, []):
            if dep not in seen:
                stack.append(dep)
    return seen


def scan_text_references() -> List[str]:
    # Findet Erwähnungen von relevanten Nicht-Python-Dateien in Code-Dateien
    references: Set[str] = set()
    # Kandidaten sammeln
    candidates: List[str] = []
    exts = (".json", ".jsonl", ".md", ".txt")
    for base in SRC_DIRS:
        base_path = os.path.join(PROJECT_ROOT, base)
        if not os.path.isdir(base_path):
            continue
        for root, _, files in os.walk(base_path):
            for fn in files:
                if fn.endswith(exts):
                    candidates.append(os.path.join(root, fn))
    # Code-Dateien
    code_files: List[str] = []
    for base in ["app", "scripts", "utils"]:
        base_path = os.path.join(PROJECT_ROOT, base)
        if os.path.isdir(base_path):
            for root, _, files in os.walk(base_path):
                for fn in files:
                    if fn.endswith(".py"):
                        code_files.append(os.path.join(root, fn))
    # Suche nach Dateinamen
    names = {os.path.basename(p): p for p in candidates}
    for cf in code_files:
        try:
            with open(cf, "r", encoding="utf-8") as f:
                content = f.read()
            for name, full in names.items():
                if name in content:
                    references.add(full)
        except Exception:
            continue
    return sorted(references)


def main() -> int:
    pyfiles = discover_pyfiles()
    graph = build_graph(pyfiles)
    entry_mods = [to_module_name(p) for _, p in ENTRYPOINTS]
    used = reachable_from(entry_mods, graph)
    unused = sorted(set(pyfiles.keys()) - used)

    print("= Audit Bericht =")
    print("Projektwurzel:", PROJECT_ROOT)
    print("Einstiegspunkte:")
    for name, p in ENTRYPOINTS:
        try:
            rel = os.path.relpath(p, PROJECT_ROOT)
        except Exception:
            rel = p
        print(f" - {name}: {rel}")

    print(f"\nGesamt Python-Module: {len(pyfiles)} | Erreichbar: {len(used)} | Potenziell ungenutzt: {len(unused)}")
    if unused:
        print("\nPotenziell ungenutzte Python-Dateien:")
        for m in unused:
            pth = pyfiles[m]
            try:
                r = os.path.relpath(pth, PROJECT_ROOT)
            except Exception:
                r = pth
            print(" -", r)

    refs = scan_text_references()
    if refs:
        print("\nNicht-Python-Dateien mit Referenzen im Code:")
        for p in refs:
            try:
                r = os.path.relpath(p, PROJECT_ROOT)
            except Exception:
                r = p
            print(" -", r)

    print("\nHinweise:")
    hp = os.path.join(PROJECT_ROOT, "app", "routers", "health.py")
    if os.path.exists(hp):
        print(" - app/routers/health.py: Separater Health-Router; in app/main.py existiert bereits /health. Prüfen ob eingebunden.")
    ap_prompt = os.path.join(PROJECT_ROOT, "app", "core", "prompts.py")
    if os.path.exists(ap_prompt):
        print(" - app/core/prompts.py: zentrale Prompt-Quelle (keine system.txt mehr).")
    cm = os.path.join(PROJECT_ROOT, "app", "core", "content_management.py")
    if os.path.exists(cm):
        print(" - app/core/content_management.py: Nur nötig, wenn Inhaltsfilter aktiv genutzt wird.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
