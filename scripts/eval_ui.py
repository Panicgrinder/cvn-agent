#!/usr/bin/env python
"""
Einfache Evaluierungs-UI (Konsolenmenü) für den CVN Agent.

Funktionen:
- Läufe starten (Pakete wählen, Limit setzen) – ASGI & Eval-Modus
- Frühere Ergebnisse ansehen (results_*.jsonl)
- Fehlgeschlagene Elemente aus einem Ergebnislauf erneut ausführen

Später erweiterbar um weitere Punkte (z. B. Feintuning).
"""

from __future__ import annotations

import os
import sys
import glob
import json
import asyncio
import logging
from dataclasses import asdict
from datetime import datetime
from typing import List, Any, Optional, Set, Dict, cast


def _load_run_eval_module():
    """Lädt scripts/run_eval.py als Modul, um dessen Funktionen wiederzuverwenden."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    import importlib.util
    run_eval_path = os.path.join(project_root, "scripts", "run_eval.py")
    spec = importlib.util.spec_from_file_location("run_eval", run_eval_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Konnte run_eval.py nicht laden")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


run_eval = _load_run_eval_module()

# Lockere Typaliases für bessere Lint-Kompatibilität
EvalResult = Any
EvalItem = Any


def clear_screen() -> None:
    os.system("cls" if os.name == "nt" else "clear")


def list_eval_packages() -> List[str]:
    """Listet verfügbare Eval-Pakete (Dateien) auf."""
    eval_dir: str = run_eval.DEFAULT_EVAL_DIR
    pattern: str = run_eval.DEFAULT_FILE_PATTERN
    files = sorted(glob.glob(os.path.join(eval_dir, pattern)))
    return files


def prompt_multi_select(options: List[str], title: str) -> List[str]:
    """Sehr einfache Mehrfachauswahl via Eingabe von Indizes (z. B. 1,3,4)."""
    if not options:
        return []
    print(title)
    for i, opt in enumerate(options, start=1):
        print(f"  {i}. {os.path.basename(opt)}")
    raw = input("Auswahl (z. B. 1,3) – leer = alle: ").strip()
    if not raw:
        return options
    try:
        idxs = [int(x) for x in raw.split(",") if x.strip().isdigit()]
        chosen = [options[i - 1] for i in idxs if 1 <= i <= len(options)]
        return chosen or options
    except Exception:
        return options


def prompt_int(prompt: str, default: int) -> int:
    raw = input(f"{prompt} (Default {default}): ").strip()
    if not raw:
        return default
    try:
        return max(0, int(raw))
    except ValueError:
        return default


def list_result_files() -> List[str]:
    eval_dir: str = run_eval.DEFAULT_EVAL_DIR
    files = sorted(glob.glob(os.path.join(eval_dir, "results_*.jsonl")), reverse=True)
    return files


def choose_from_list(options: List[str], title: str) -> Optional[str]:
    if not options:
        print("Keine Einträge vorhanden.")
        return None
    print(title)
    for i, path in enumerate(options, start=1):
        print(f"  {i}. {os.path.basename(path)}")
    raw = input("Auswahl (Zahl, leer = Abbrechen): ").strip()
    if not raw:
        return None
    if raw.isdigit():
        idx = int(raw)
        if 1 <= idx <= len(options):
            return options[idx - 1]
    return None


def ensure_eval_files_exist() -> None:
    eval_dir: str = run_eval.DEFAULT_EVAL_DIR
    os.makedirs(eval_dir, exist_ok=True)
    pattern: str = run_eval.DEFAULT_FILE_PATTERN
    if not any(glob.glob(os.path.join(eval_dir, pattern))):
        example_file = os.path.join(eval_dir, "eval-21-40_demo_v1.0.jsonl")
        print("Keine Eval-Dateien gefunden – erstelle Demo-Paket …")
        run_eval.create_example_eval_file(example_file, 21, 20)


def profiles_path() -> str:
    return os.path.join(run_eval.DEFAULT_EVAL_DIR, ".profiles.json")


def load_profiles() -> Dict[str, Dict[str, Any]]:
    path = profiles_path()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "default": {
            "model": None,
            "host": None,
            "temperature": None,
            "checks": None,
            "quiet": None,
        }
    }


def save_profiles(data: Dict[str, Dict[str, Any]]) -> None:
    os.makedirs(run_eval.DEFAULT_EVAL_DIR, exist_ok=True)
    with open(profiles_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def choose_profile(profiles: Dict[str, Dict[str, Any]]) -> str:
    keys = list(profiles.keys())
    print("Profile:")
    for i, k in enumerate(keys, start=1):
        print(f"  {i}. {k}")
    raw = input("Auswahl (leer = default): ").strip()
    if raw.isdigit():
        idx = int(raw)
        if 1 <= idx <= len(keys):
            return keys[idx - 1]
    return "default"


def action_edit_profiles() -> None:
    clear_screen()
    data = load_profiles()
    print("Profile bearbeiten/anlegen\n")
    name = input("Profilname (leer = default): ").strip() or "default"
    prof = data.get(name, {"model": None, "host": None, "temperature": None, "checks": None, "quiet": None})
    prof["model"] = input(f"Model [{prof.get('model') or '-'}]: ").strip() or prof.get("model")
    prof["host"] = input(f"Host [{prof.get('host') or '-'}]: ").strip() or prof.get("host")
    t = input(f"Temperature [{prof.get('temperature') if prof.get('temperature') is not None else '-'}]: ").strip()
    if t:
        try:
            prof["temperature"] = float(t)
        except ValueError:
            pass
    checks = input("Checks (Kommagetrennt, leer = alle / unverändert): ").strip()
    if checks:
        prof["checks"] = [p.strip() for p in checks.split(",") if p.strip()]
    q = input(f"Quiet-Mode (y/n, leer = unverändert [{prof.get('quiet')}]): ").strip().lower()
    if q in ("y", "yes"):
        prof["quiet"] = True
    elif q in ("n", "no"):
        prof["quiet"] = False
    data[name] = prof
    save_profiles(data)
    print("Gespeichert.")
    input("Weiter mit Enter …")


def action_start_run() -> None:
    clear_screen()
    ensure_eval_files_exist()
    packages: List[str] = list_eval_packages()
    if not packages:
        print("Keine Eval-Pakete gefunden.")
        input("Weiter mit Enter …")
        return
    chosen: List[str] = prompt_multi_select(packages, "Verfügbare Pakete:")
    # Default-Limit: Anzahl der Prompts pro ausgewählter Datei grob als 20 pro Datei
    default_limit = max(1, 20 * len(chosen))
    limit = prompt_int("Limit (0 = alle aus Auswahl)", default_limit)
    patterns: List[str] = chosen

    # Profil wählen (optional)
    prof_data = load_profiles()
    use_profile = input("Profil verwenden? (y/N): ").strip().lower() == "y"
    profile_name = "default"
    profile = prof_data.get("default", {})
    if use_profile:
        profile_name = choose_profile(prof_data)
        profile = prof_data.get(profile_name, {})

    # Optionale Check-Auswahl
    check_types = ["must_include", "keywords_any", "keywords_at_least", "not_include", "regex"]
    print("\nWelche Checks sollen aktiv sein? (leer = alle)")
    for i, c in enumerate(check_types, start=1):
        print(f"  {i}. {c}")
    default_checks = ",".join(profile.get("checks") or []) if profile.get("checks") else ""
    raw_checks = input(f"Auswahl (z. B. 1,3) oder Namen, Kommagetrennt [{default_checks}]: ").strip() or default_checks
    enabled_checks: Optional[List[str]] = None
    if raw_checks:
        parts = [p.strip() for p in raw_checks.split(",") if p.strip()]
        chosen_checks: List[str] = []
        for p in parts:
            if p.isdigit():
                idx = int(p)
                if 1 <= idx <= len(check_types):
                    chosen_checks.append(check_types[idx - 1])
            elif p in check_types:
                chosen_checks.append(p)
        enabled_checks = list(dict.fromkeys(chosen_checks)) or None

    # Overrides aus Profil
    model_override = profile.get("model")
    host_override = profile.get("host")
    temperature_override = profile.get("temperature")

    # Debug/Quiet-Optionen
    dbg = input("Debug-Modus aktivieren? (y/N): ").strip().lower() == "y"
    prof_quiet = profile.get("quiet")
    quiet_mode = (True if prof_quiet is None else bool(prof_quiet)) and (not dbg)

    print(f"\nStarte Evaluierung (Profil: {profile_name}, Debug: {dbg}, Quiet: {quiet_mode}) …\n")

    # Optional: temporär Logger-Level für Debug erhöhen
    prev_levels: Dict[str, int] = {}
    noisy_loggers = ["app", "app.api.chat", "httpx", "uvicorn"]
    try:
        if dbg:
            for name in noisy_loggers:
                lg = logging.getLogger(name)
                prev_levels[name] = lg.level
                lg.setLevel(logging.DEBUG)

        results: List[EvalResult] = asyncio.run(
            run_eval.run_evaluation(
                patterns=patterns,
                api_url=run_eval.DEFAULT_API_URL,
                limit=(None if limit == 0 else limit),
                eval_mode=True,
                skip_preflight=True,
                asgi=True,
                enabled_checks=enabled_checks,
                model_override=model_override,
                temperature_override=temperature_override,
                host_override=host_override,
                quiet=quiet_mode,
            )
        )
    finally:
        if dbg:
            for name, lvl in prev_levels.items():
                logging.getLogger(name).setLevel(lvl)
    if results:
        run_eval.print_results(results)
    else:
        print("Keine Ergebnisse – möglicherweise abgebrochen oder keine Einträge gefunden.")
    input("Weiter mit Enter …")


def load_results_from_file(path: str) -> List[EvalResult]:  # lockerer Typ
    """Lädt JSONL-Ergebnisse in EvaluationResult-Objekte."""
    results: List[EvalResult] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            raw = json.loads(line)
            if not isinstance(raw, dict):
                continue
            data: Dict[str, Any] = cast(Dict[str, Any], raw)
            # Meta-Header-Zeilen überspringen
            if data.get("_meta") is True:
                continue
            # Felder an Dataclass übergeben (fehlende Felder mit Defaults)
            res: EvalResult = run_eval.EvaluationResult(
                item_id=data.get("item_id", ""),
                response=data.get("response", ""),
                checks_passed=data.get("checks_passed", {}),
                success=bool(data.get("success", False)),
                failed_checks=list(data.get("failed_checks", [])),
                error=data.get("error"),
                source_file=data.get("source_file"),
                source_package=data.get("source_package"),
                duration_ms=int(data.get("duration_ms", 0)),
            )
            results.append(res)
    return results


def load_run_meta(path: str) -> Optional[Dict[str, Any]]:
    """Lädt die Meta-Header-Zeile einer results_*.jsonl-Datei (falls vorhanden)."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            first = f.readline().strip()
            if not first:
                return None
            raw = json.loads(first)
            if not isinstance(raw, dict):
                return None
            data: Dict[str, Any] = cast(Dict[str, Any], raw)
            if data.get("_meta") is True:
                return data
    except Exception:
        return None
    return None


def action_trends() -> None:
    clear_screen()
    files = list_result_files()
    if not files:
        print("Keine Ergebnisdateien gefunden.")
        input("Weiter mit Enter …")
        return
    print("Analysiere Läufe …\n")
    summaries: List[Dict[str, Any]] = []
    for path in files:
        meta = load_run_meta(path) or {}
        results = load_results_from_file(path)
        if not results:
            continue
        total = len(results)
        success = sum(1 for r in results if r.success)
        rate = (success / total) * 100.0
        avg_ms = int(sum(r.duration_ms for r in results) / total)
        rpg = sum(1 for r in results if run_eval.check_rpg_mode(r.response))
        summaries.append({
            "file": os.path.basename(path),
            "timestamp": meta.get("timestamp") or "-",
            "model": (meta.get("overrides", {}).get("model") or meta.get("model") or "-"),
            "host": (meta.get("overrides", {}).get("host") or meta.get("host") or "-"),
            "temp": (meta.get("overrides", {}).get("temperature") or meta.get("temperature") or "-"),
            "checks": ",".join(meta.get("enabled_checks") or []),
            "total": total,
            "success": success,
            "rate": rate,
            "avg_ms": avg_ms,
            "rpg": rpg,
        })

    if not summaries:
        print("Keine auswertbaren Läufe gefunden.")
        input("Weiter mit Enter …")
        return

    # Übersichts-Tabelle (letzte 10)
    print("Letzte Läufe:\n")
    header = f"{'Zeit':<13}  {'Model':<18}  {'OK':>6}/{ 'Tot':<4}  {'Rate':>6}  {'Øms':>6}  {'RPG':>4}  Datei"
    print(header)
    print("-" * len(header))
    for s in summaries[:10]:
        zeit = s["timestamp"][-5:] if isinstance(s["timestamp"], str) and len(s["timestamp"])>=13 else s["timestamp"]
        model = str(s["model"])[:18]
        print(f"{zeit:<13}  {model:<18}  {s['success']:>6}/{s['total']:<4}  {s['rate']:>5.1f}%  {s['avg_ms']:>6}  {s['rpg']:>4}  {s['file']}")

    # Gesamtübersicht
    grand_total = sum(s["total"] for s in summaries)
    grand_success = sum(s["success"] for s in summaries)
    grand_rate = (grand_success / grand_total) * 100.0 if grand_total else 0.0
    print(f"\nGesamt: {grand_success}/{grand_total} ({grand_rate:.1f}%)\n")

    # CSV-Export
    if input("Runs als CSV exportieren? (y/N): ").strip().lower() == "y":
        out_csv = os.path.join(run_eval.DEFAULT_EVAL_DIR, "runs_summary.csv")
        import csv
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["file","timestamp","model","host","temperature","checks","total","success","rate","avg_ms","rpg"]) 
            for s in summaries:
                w.writerow([s["file"], s["timestamp"], s["model"], s["host"], s["temp"], s["checks"], s["total"], s["success"], f"{s['rate']:.1f}", s["avg_ms"], s["rpg"]])
        print(f"CSV exportiert: {out_csv}")

    # Detail: Paket-Statistik für einen Lauf
    if input("Paket-Statistik eines Laufs ansehen? (y/N): ").strip().lower() == "y":
        fname = choose_from_list([s["file"] for s in summaries], "Wähle Lauf:")
        if fname:
            path = os.path.join(run_eval.DEFAULT_EVAL_DIR, fname)
            results = load_results_from_file(path)
            if not results:
                print("Keine Ergebnisse in dieser Datei.")
            else:
                stats: Dict[str, Dict[str, int]] = {}
                for r in results:
                    pkg = r.source_package or "unbekannt"
                    d = stats.setdefault(pkg, {"tot":0, "ok":0, "dur":0})
                    d["tot"] += 1
                    d["dur"] += r.duration_ms
                    if r.success:
                        d["ok"] += 1
                print("\nPaket-Statistik:\n")
                ph = f"{'Paket':<30}  {'OK':>6}/{ 'Tot':<4}  {'Rate':>6}  {'Øms':>6}"
                print(ph)
                print("-" * len(ph))
                for pkg, d in sorted(stats.items()):
                    rate = (d["ok"] / d["tot"]) * 100.0 if d["tot"] else 0.0
                    avg = int(d["dur"] / d["tot"]) if d["tot"] else 0
                    print(f"{pkg:<30}  {d['ok']:>6}/{d['tot']:<4}  {rate:>5.1f}%  {avg:>6}")
    input("Weiter mit Enter …")


def action_view_results() -> None:
    clear_screen()
    files = list_result_files()
    chosen = choose_from_list(files, "Vorhandene Ergebnisdateien:")
    if not chosen:
        return
    raw_results = load_results_from_file(chosen)
    # Filter Meta-Header-Zeilen
    results: List[EvalResult] = [r for r in raw_results if not getattr(r, "_meta", False)]
    # Optionaler Filter
    print("Filter: 1) alle  2) nur Fails  3) nur Success")
    fsel = input("Auswahl (leer=alle): ").strip()
    if fsel == "2":
        results = [r for r in results if not r.success]
    elif fsel == "3":
        results = [r for r in results if r.success]
    # Export-Option
    export = input("Als CSV exportieren? (y/N): ").strip().lower() == "y"
    if export:
        out_csv = os.path.splitext(chosen)[0] + "_export.csv"
        import csv
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["id", "success", "package", "duration_ms", "failed_checks"]) 
            for r in results:
                writer.writerow([r.item_id, r.success, r.source_package or "-", r.duration_ms, "; ".join(r.failed_checks)])
        print(f"CSV exportiert: {out_csv}")
    # Markdown-Export
    md = input("Als Markdown-Report exportieren? (y/N): ").strip().lower() == "y"
    if md:
        out_md = os.path.splitext(chosen)[0] + "_report.md"
        successful = sum(1 for r in results if r.success)
        total = len(results)
        with open(out_md, "w", encoding="utf-8") as f:
            f.write(f"# Evaluierungsreport\n\n")
            f.write(f"Quelle: {os.path.basename(chosen)}\n\n")
            f.write(f"Erfolg: {successful}/{total} ({(successful/total*100 if total else 0):.1f}%)\n\n")
            f.write("## Fehlgeschlagene Tests\n\n")
            for r in results:
                if not r.success:
                    f.write(f"- {r.item_id}: {', '.join(r.failed_checks)}\n")
        print(f"Markdown exportiert: {out_md}")
    if results:
        run_eval.print_results(results)
    else:
        print("Datei enthält keine Ergebnisse.")
    input("Weiter mit Enter …")


async def _evaluate_specific_items(items: List[EvalItem]) -> List[EvalResult]:
    """Evaluiert die übergebenen Items (ASGI, Eval-Modus) und schreibt eine neue results_*.jsonl-Datei."""
    # Ergebnis-Dateiname
    eval_dir: str = run_eval.DEFAULT_EVAL_DIR
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    out_path = os.path.join(eval_dir, f"results_{timestamp}.jsonl")

    # ASGI-Client vorbereiten
    from app.main import app as fastapi_app  # type: ignore
    import httpx
    transport = httpx.ASGITransport(app=fastapi_app)
    client = httpx.AsyncClient(transport=transport, base_url="http://asgi")
    api_url = "/chat"

    results: List[EvalResult] = []
    try:
        from rich.progress import Progress
        with Progress() as progress:
            task = progress.add_task("[cyan]Evaluiere (Retry)…", total=len(items))
            for item in items:
                res: EvalResult = await run_eval.evaluate_item(item, api_url=api_url, eval_mode=True, client=client)
                results.append(res)
                # sofort persistieren
                with open(out_path, "a", encoding="utf-8") as f:
                    d = asdict(res)
                    d["response"] = run_eval.truncate(d.get("response", ""), 500)
                    f.write(json.dumps(d, ensure_ascii=False) + "\n")
                progress.update(task, advance=1)
    finally:
        await client.aclose()

    logging.info(f"Ergebnisse wurden in {out_path} gespeichert.")
    return results


def action_rerun_failed() -> None:
    clear_screen()
    files = list_result_files()
    chosen = choose_from_list(files, "Ergebnisdatei für erneute Ausführung fehlgeschlagener Items wählen:")
    if not chosen:
        return

    # Lade Ergebnisse und extrahiere fehlgeschlagene IDs
    prev_results: List[EvalResult] = load_results_from_file(chosen)
    failed_ids: List[str] = [r.item_id for r in prev_results if not r.success]
    if not failed_ids:
        print("Keine fehlgeschlagenen Items in der gewählten Datei.")
        input("Weiter mit Enter …")
        return

    print(f"Gefundene fehlgeschlagene Items: {len(failed_ids)}")

    # Lade alle Items aus den Standardpaketen und filtere nach IDs
    patterns: List[str] = [os.path.join(run_eval.DEFAULT_EVAL_DIR, run_eval.DEFAULT_FILE_PATTERN)]
    all_items: List[EvalItem] = asyncio.run(run_eval.load_evaluation_items(patterns))
    id_set: Set[str] = set(failed_ids)
    items_to_rerun: List[EvalItem] = [it for it in all_items if it.id in id_set]

    if not items_to_rerun:
        print("Keine passenden Items in den Eval-Paketen gefunden.")
        input("Weiter mit Enter …")
        return

    print(f"Starte erneute Ausführung von {len(items_to_rerun)} Items …\n")
    results: List[EvalResult] = asyncio.run(_evaluate_specific_items(items_to_rerun))
    if results:
        run_eval.print_results(results)
    input("Weiter mit Enter …")


def action_export_finetune() -> None:
    clear_screen()
    files = list_result_files()
    chosen = choose_from_list(files, "Ergebnisdatei für Finetuning-Export wählen:")
    if not chosen:
        return
    fmt = input("Format wählen: 1) alpaca  2) openai_chat [1]: ").strip()
    fmt = "openai_chat" if fmt == "2" else "alpaca"
    inc = input("Auch Fehlschläge exportieren? (y/N): ").strip().lower() == "y"
    # Export ausführen
    try:
        import importlib
        exporter = importlib.import_module("scripts.export_finetune")
        export_fn = getattr(exporter, "export_from_results")
    except Exception as e:
        print("Exporter nicht verfügbar:", e)
        input("Weiter mit Enter …")
        return
    out: Dict[str, Any] = asyncio.run(export_fn(chosen, format=fmt, include_failures=inc))
    if out.get("ok"):
        print(f"Export erfolgreich: {out['out']} ({out['count']} Einträge)")
    else:
        print("Fehler:", out.get("error"))
    input("Weiter mit Enter …")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%H:%M:%S")
    while True:
        clear_screen()
        print("CVN Agent – Evaluierungsmenü")
        print("============================\n")
        print("1) Lauf starten (Pakete & Limit)")
        print("2) Ergebnisse ansehen")
        print("3) Fehlgeschlagene erneut ausführen")
        print("4) Trends / Aggregation")
        print("5) Finetuning-Export aus Ergebnissen")
        print("6) Profile verwalten")
        print("7) Beenden")
        choice = input("\nAuswahl: ").strip()
        if choice == "1":
            action_start_run()
        elif choice == "2":
            action_view_results()
        elif choice == "3":
            action_rerun_failed()
        elif choice == "4":
            action_trends()
        elif choice == "5":
            action_export_finetune()
        elif choice == "6":
            action_edit_profiles()
        elif choice == "7":
            break


if __name__ == "__main__":
    main()
