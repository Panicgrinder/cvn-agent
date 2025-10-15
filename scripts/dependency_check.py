#!/usr/bin/env python
import os
import sys
import glob
import json
from typing import List, Dict, Any, Tuple, cast

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

def read(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def ok(msg: str): print(f"[OK] {msg}")
def warn(msg: str): print(f"[WARN] {msg}")
def err(msg: str): print(f"[ERR] {msg}")

def check_runner_constants() -> Dict[str, Any]:
    import importlib.util
    rp = os.path.join(ROOT, "scripts", "run_eval.py")
    spec = importlib.util.spec_from_file_location("run_eval", rp)
    if spec is None or spec.loader is None:
        err("Konnte ModuleSpec für run_eval.py nicht erstellen")
        return {}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    req_attrs = [
        "DEFAULT_EVAL_DIR", "DEFAULT_DATASET_DIR", "DEFAULT_RESULTS_DIR",
        "DEFAULT_CONFIG_DIR", "DEFAULT_FILE_PATTERN",
        "load_prompts", "load_evaluation_items", "evaluate_item", "run_evaluation", "print_results"
    ]
    missing = [a for a in req_attrs if not hasattr(mod, a)]
    for a in req_attrs:
        if a not in missing:
            ok(f"run_eval.{a} vorhanden")
    if missing:
        err(f"run_eval: fehlende Attribute/Funktionen: {missing}")

    # Prüfe, dass load_prompts standardmäßig datasets/ nutzt (robuster Scan der Funktionsdefinition)
    code = read(rp)
    start = code.find("async def load_prompts(")
    if start != -1:
        # Versuche das Ende der Funktion heuristisch zu finden: Beginn der nächsten async def/def
        next_async = code.find("\nasync def ", start + 1)
        next_def = code.find("\ndef ", start + 1)
        end_candidates = [c for c in [next_async, next_def] if c != -1]
        end = min(end_candidates) if end_candidates else len(code)
        func_block = code[start:end]
        if "DEFAULT_DATASET_DIR" in func_block and "DEFAULT_FILE_PATTERN" in func_block:
            ok("load_prompts default -> DEFAULT_DATASET_DIR")
        else:
            err("load_prompts default nutzt NICHT DEFAULT_DATASET_DIR (Patch nötig)")
    else:
        warn("Konnte load_prompts nicht im Code finden")

    return {"mod": mod}

def check_ui_refs():
    import importlib.util
    up = os.path.join(ROOT, "scripts", "eval_ui.py")
    spec = importlib.util.spec_from_file_location("eval_ui", up)
    if spec is None or spec.loader is None:
        warn("Konnte ModuleSpec für eval_ui.py nicht erstellen")
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    code = read(up)
    if "DEFAULT_DATASET_DIR" in code and "DEFAULT_RESULTS_DIR" in code:
        ok("eval_ui referenziert DEFAULT_DATASET_DIR/DEFAULT_RESULTS_DIR")
    else:
        warn("eval_ui: Prüfe Referenzen auf DEFAULT_*-Konstanten")

def check_api_eval_prompt():
    ap = os.path.join(ROOT, "app", "api", "chat.py")
    code = read(ap)
    if "process_chat_request" not in code:
        err("app/api/chat.py: process_chat_request fehlt")
        return
    if "EVAL_SYSTEM_PROMPT" in code and "eval_mode" in code:
        ok("app/api/chat.py: Eval-Systemprompt wird referenziert")
    else:
        err("app/api/chat.py: Eval-Systemprompt-Injektion nicht gefunden (eval_mode)")

def check_synonyms():
    from utils.eval_utils import load_synonyms
    # Ideale Orte laut Runner
    import importlib.util
    rp = os.path.join(ROOT, "scripts", "run_eval.py")
    spec = importlib.util.spec_from_file_location("run_eval", rp)
    if spec is None or spec.loader is None:
        warn("Konnte ModuleSpec für run_eval.py nicht erstellen (synonyms)")
        return
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    cfg = getattr(mod, "DEFAULT_CONFIG_DIR", os.path.join(ROOT, "eval", "config"))
    base = os.path.join(cfg, "synonyms.json")
    overlay = os.path.join(cfg, "synonyms.local.json")
    merged = load_synonyms([base, overlay])
    if isinstance(merged, dict) and merged:
        ok(f"Synonyme geladen ({len(merged)} Einträge) aus config/")
    else:
        warn("Synonyme leer oder nicht geladen")
    if os.path.exists(overlay):
        ok("synonyms.local.json vorhanden und wird gemerged")
    else:
        ok("synonyms.local.json nicht vorhanden (optional, gitignored)")

def coerce_json_to_jsonl(text: str) -> List[Dict[str, Any]]:
    # kleiner localer Fallback, falls utils nicht importiert werden soll
    try:
        data: Any = json.loads(text)
    except Exception:
        data = None

    if isinstance(data, list):
        result: List[Dict[str, Any]] = []
        for x in cast(List[Any], data):
            if isinstance(x, dict):
                result.append(cast(Dict[str, Any], x))
        return result
    if isinstance(data, dict):
        return [cast(Dict[str, Any], data)]

    # JSONL-Fallback
    out: List[Dict[str, Any]] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj_any: Any = json.loads(line)
            if isinstance(obj_any, dict):
                out.append(cast(Dict[str, Any], obj_any))
        except Exception:
            pass
    return out

def check_datasets_and_precedence():
    datasets_dir = os.path.join(ROOT, "eval", "datasets")
    files = sorted(glob.glob(os.path.join(datasets_dir, "eval-*.json*")))
    if not files:
        err("Keine Dataset-Dateien in eval/datasets gefunden")
        return
    ok(f"{len(files)} Dataset-Dateien gefunden")
    # Prüfe Schema grob und Duplikat-Priorisierung
    seen: Dict[str, Tuple[Dict[str, Any], float, str]] = {}
    for fp in files:
        mtime = os.path.getmtime(fp)
        text = read(fp).strip()
        objs = coerce_json_to_jsonl(text)
        for idx, obj in enumerate(objs):
            if not isinstance(obj, dict):
                warn(f"{os.path.basename(fp)}: Eintrag {idx} ist kein Objekt")
                continue
            pid = str(obj.get("id") or f"{os.path.splitext(os.path.basename(fp))[0]}-{idx:04d}")
            has_messages = isinstance(obj.get("messages"), list)
            has_prompt = isinstance(obj.get("prompt"), str)
            checks: Dict[str, Any] | Any = obj.get("checks") or obj.get("must_include") or {}
            if not (has_messages or has_prompt):
                warn(f"{os.path.basename(fp)}:{idx} hat weder messages noch prompt")
            if not checks:
                warn(f"{os.path.basename(fp)}:{idx} hat keine checks/must_include")
            if pid in seen:
                _, prev_mtime, prev = seen[pid]
                if mtime > prev_mtime:
                    ok(f"Prio: Neuere Datei überschreibt ältere ID {pid} ({os.path.basename(prev)} -> {os.path.basename(fp)})")
                    seen[pid] = (obj, mtime, fp)
                else:
                    ok(f"Prio: Ältere Datei bleibt für ID {pid} (neueres wurde verworfen): {os.path.basename(prev)}")
            else:
                seen[pid] = (obj, mtime, fp)

def check_prompt_files_not_referenced():
    # Historische Dateien sollten nicht referenziert werden
    candidates = [
        os.path.join(ROOT, "data", "system.txt"),
        os.path.join(ROOT, "app", "prompt", "system.txt"),
    ]
    code_files: List[str] = []
    for base in ("app", "scripts", "utils"):
        for dp, _, fns in os.walk(os.path.join(ROOT, base)):
            for fn in fns:
                if fn.endswith(".py"):
                    code_files.append(os.path.join(dp, fn))
    for c in candidates:
        rel = os.path.relpath(c, ROOT)
        if not os.path.exists(c):
            ok(f"{rel} existiert nicht (gut)")
            continue
        # Suche nach exakten Pfadangaben (vor/zurück Slashes), nicht nach dem generischen Basenamen
        patterns = {
            rel.replace("\\", "/"),
            rel.replace("/", "\\"),
            os.path.normpath(rel),
        }
        found = False
        for cf in code_files:
            try:
                content = read(cf)
                if any(p in content for p in patterns):
                    found = True
                    break
            except Exception:
                pass
        if found:
            warn(f"Historische Prompt-Datei wird noch referenziert: {rel}")
        else:
            ok(f"Historische Prompt-Datei NICHT referenziert: {rel}")

def main():
    print("= Dependency Check (wichtigste Daten) =")
    check_runner_constants()
    check_ui_refs()
    check_api_eval_prompt()
    check_synonyms()
    check_datasets_and_precedence()
    check_prompt_files_not_referenced()
    print("\nFertig.")

if __name__ == "__main__":
    main()