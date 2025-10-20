#!/usr/bin/env python
# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""
Einfacher Poller für OpenAI Fine-Tuning-Jobstatus und Events.

Beispiel:
  python scripts/openai_ft_status.py <JOB_ID> --interval 15
  python scripts/openai_ft_status.py <JOB_ID> --no-follow --events-limit 50
"""
from __future__ import annotations

import os
import time
import argparse
from typing import Any, Dict, List, Tuple, Optional, Callable

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

# Optionaler Import: In CI/Tests wird OpenAI oft gemockt/monkeypatched.
# Daher beim Modulimport NICHT beenden, sondern nur beim tatsächlichen Aufruf prüfen.
try:  # pragma: no cover - Importpfad wird in Tests meist ersetzt
    from openai import OpenAI as _OpenAI  # type: ignore
    OpenAI: Optional[Callable[..., Any]] = _OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore[assignment]


def fetch_status_and_events(client: Any, job_id: str, limit: int = 25) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    job = client.fine_tuning.jobs.retrieve(job_id)
    ev = client.fine_tuning.jobs.list_events(job_id, limit=limit)
    events: List[Dict[str, Any]] = getattr(ev, "data", ev)  # SDK liefert .data
    jdict: Dict[str, Any] = job.to_dict() if hasattr(job, "to_dict") else dict(job)
    edicts: List[Dict[str, Any]] = []
    for e in events:
        ee: Any = e
        edicts.append(ee.to_dict() if hasattr(ee, "to_dict") else dict(ee))
    return jdict, edicts


def print_snapshot(job: Dict[str, Any], events: List[Dict[str, Any]], show_events: bool = True) -> None:
    jid = job.get("id")
    status = job.get("status")
    base = f"Job {jid} status={status}"
    if model := job.get("model"):
        base += f" model={model}"
    if ftm := job.get("fine_tuned_model"):
        base += f" fine_tuned_model={ftm}"
    print(base)
    if show_events and events:
        for e in reversed(sorted(events, key=lambda x: x.get("created_at", 0))):
            ts = e.get("created_at")
            level = e.get("level")
            msg = e.get("message")
            print(f" - [{level}] {ts}: {msg}")


def follow(job_id: str, interval: int = 10, show_events: bool = True, events_limit: int = 25) -> None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY fehlt (in .env setzen)")
    if OpenAI is None:
        raise SystemExit("Bitte 'openai' installieren: pip install openai")
    client = OpenAI(api_key=api_key)  # type: ignore[operator]

    seen_event_ids: set[str] = set()
    terminal_states = {"succeeded", "failed", "cancelled"}
    while True:
        job, events = fetch_status_and_events(client, job_id, limit=events_limit)
        # Filter nur neue Events
        new_events: List[Dict[str, Any]] = []
        for e in events:
            eid = e.get("id") or f"{e.get('created_at')}-{e.get('message')}"
            if eid not in seen_event_ids:
                seen_event_ids.add(eid)
                new_events.append(e)
        print_snapshot(job, new_events if show_events else [], show_events=show_events)
        if str(job.get("status")).lower() in terminal_states:
            break
        time.sleep(max(1, interval))


def main() -> None:
    ap = argparse.ArgumentParser(description="OpenAI FT Job Status/Events")
    ap.add_argument("job_id", help="Fine-Tuning Job-ID (z.B. ftjob-...)")
    ap.add_argument("--interval", type=int, default=10, help="Pollingintervall in Sekunden")
    ap.add_argument("--no-follow", action="store_true", help="Nur eine Momentaufnahme anzeigen")
    ap.add_argument("--no-events", action="store_true", help="Events nicht ausgeben")
    ap.add_argument("--events-limit", type=int, default=25, help="Max. Anzahl geladener Events pro Poll")
    args = ap.parse_args()

    if args.no_follow:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise SystemExit("OPENAI_API_KEY fehlt (in .env setzen)")
        if OpenAI is None:
            raise SystemExit("Bitte 'openai' installieren: pip install openai")
        client = OpenAI(api_key=api_key)  # type: ignore[operator]
        job, events = fetch_status_and_events(client, args.job_id, limit=args.events_limit)
        print_snapshot(job, events if not args.no_events else [], show_events=not args.no_events)
    else:
        follow(args.job_id, interval=args.interval, show_events=not args.no_events, events_limit=args.events_limit)


if __name__ == "__main__":
    main()
