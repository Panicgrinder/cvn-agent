#!/usr/bin/env python
"""
Quick-Start Evaluierung für den CVN Agent.
- ASGI-In-Process
- Eval-Modus (RPG deaktiviert)
- Limit via QUICK_EVAL_LIMIT (default 10)
Ergebnisse: eval/results/results_YYYYMMDD_HHMM.jsonl
"""

import os
import sys
import importlib.util
import asyncio


def _load_run_eval_module():
    """Lädt scripts/run_eval.py als Modul, ohne CLI zu benötigen."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    run_eval_path = os.path.join(project_root, "scripts", "run_eval.py")
    spec = importlib.util.spec_from_file_location("run_eval", run_eval_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Kann run_eval.py nicht laden")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


async def _main_async() -> int:
    run_eval = _load_run_eval_module()
    # Verzeichnisse sicherstellen
    os.makedirs(
        getattr(run_eval, "DEFAULT_DATASET_DIR", os.path.join("eval", "datasets")),
        exist_ok=True,
    )
    os.makedirs(
        getattr(run_eval, "DEFAULT_RESULTS_DIR", os.path.join("eval", "results")),
        exist_ok=True,
    )
    # Default-Pattern aus Runner
    patt = os.path.join(
        getattr(run_eval, "DEFAULT_DATASET_DIR", os.path.join("eval", "datasets")),
        getattr(run_eval, "DEFAULT_FILE_PATTERN", "eval-*.json"),
    )
    limit_env = os.getenv("QUICK_EVAL_LIMIT", "10")
    try:
        limit = int(limit_env)
    except Exception:
        limit = 10
    # ASGI-Client wird intern gebaut
    results = await run_eval.run_evaluation(
        patterns=[patt],
        api_url="/chat",
        limit=limit,
        eval_mode=True,
        asgi=True,
        quiet=True,
        skip_preflight=True,
    )
    # Kurz ausgeben
    run_eval.print_results(results)
    return 0


def main() -> int:
    return asyncio.run(_main_async())


if __name__ == "__main__":
    raise SystemExit(main())
