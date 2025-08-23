#!/usr/bin/env python
"""
Quick-Start Evaluierung für den CVN Agent.

Einfach in VS Code ausführen (Run-Button). Läuft automatisch:
- im ASGI-In-Process-Modus (kein HTTP-Port nötig)
- mit Eval-Modus (RPG-Systemprompt deaktiviert)
- mit optionalem Limit über Umgebungsvariable QUICK_EVAL_LIMIT (Standard: 10)

Ergebnisse werden wie gewohnt unter eval/results_YYYYMMDD_HHMM.jsonl gespeichert
und in der Konsole zusammengefasst.
"""

import os
import sys
import glob
import asyncio
import logging
import importlib.util
from typing import List, cast


def _load_run_eval_module():
    """Lädt scripts/run_eval.py als Modul, ohne dass Kommandozeilenargumente nötig sind."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    run_eval_path = os.path.join(project_root, "scripts", "run_eval.py")
    spec = importlib.util.spec_from_file_location("run_eval", run_eval_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Konnte run_eval.py nicht laden")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def main():
    # Logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )

    run_eval = _load_run_eval_module()

    eval_dir: str = cast(str, run_eval.DEFAULT_EVAL_DIR)
    file_pattern: str = cast(str, run_eval.DEFAULT_FILE_PATTERN)
    api_url: str = cast(str, run_eval.DEFAULT_API_URL)

    os.makedirs(eval_dir, exist_ok=True)

    patterns: List[str] = [os.path.join(eval_dir, file_pattern)]

    # Falls keine Eval-Dateien vorhanden sind, Beispiel erzeugen
    if not any(glob.glob(p) for p in patterns):
        logging.info("Keine Eval-Dateien gefunden. Erstelle ein Beispiel-Eval-Paket…")
        example_file = os.path.join(eval_dir, "eval-21-40_demo_v1.0.jsonl")
        run_eval.create_example_eval_file(example_file, 21, 20)

    # Optionales Limit aus Env (Standard 10)
    try:
        limit = int(os.environ.get("QUICK_EVAL_LIMIT", "10"))
    except ValueError:
        limit = 10

    # Eval-Modus immer an, Preflight aus, ASGI an
    print("CVN Agent Quick Evaluierung")
    print(f"Patterns: {', '.join(patterns)}")
    print(f"API-URL: {api_url} (ASGI-In-Process)")
    print(f"Limit: {limit} Einträge")
    print("Eval-Modus aktiviert: RPG-Systemprompt wird temporär überschrieben")
    print("ASGI-Modus: In-Process gegen FastAPI-App (kein HTTP-Port erforderlich)\n")

    results = asyncio.run(
        run_eval.run_evaluation(
            patterns=patterns,
            api_url=api_url,
            limit=limit,
            eval_mode=True,
            skip_preflight=True,
            asgi=True,
            enabled_checks=None,
            model_override=None,
            temperature_override=None,
            host_override=None,
            quiet=True,
        )
    )

    if results:
        run_eval.print_results(results)
    else:
        print("Keine Ergebnisse. Die Evaluierung wurde abgebrochen oder keine Einträge gefunden.")


if __name__ == "__main__":
    main()
