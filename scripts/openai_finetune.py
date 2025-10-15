#!/usr/bin/env python
# pyright: reportMissingImports=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""
Hilfsskript für OpenAI-Finetuning mit openai_chat-JSONL.

Voraussetzungen:
- OPENAI_API_KEY als Umgebungsvariable
- Datensätze: *_train.jsonl und *_val.jsonl (openai_chat-Format)
"""
from __future__ import annotations

import os
import json
from typing import Any, Dict, Optional
import importlib

# OpenAI-Client dynamisch importieren (zur Compile-Zeit optional)
try:
    _openai_mod = importlib.import_module("openai")
    _OpenAI_factory: Optional[Any] = getattr(_openai_mod, "OpenAI", None)
except Exception:  # pragma: no cover - optional dependency at runtime
    _OpenAI_factory = None

# .env laden (nur Workspace, keine Systemweite Variable nötig)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def validate_openai_chat_jsonl(path: str, limit: int = 5) -> None:
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            if not line.strip():
                continue
            obj: Dict[str, Any] = json.loads(line)
            assert isinstance(obj, dict), f"Zeile {i}: kein Objekt"
            assert "messages" in obj, f"Zeile {i}: 'messages' fehlt"
            assert isinstance(obj["messages"], list), f"Zeile {i}: 'messages' ist nicht Liste"
            for m in obj["messages"]:
                assert isinstance(m, dict) and "role" in m and "content" in m, f"Zeile {i}: ungültige message"
            if i >= limit:
                break


def start_finetune(train_path: str, val_path: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"ok": False, "error": "OPENAI_API_KEY fehlt"}
    if _OpenAI_factory is None:
        return {"ok": False, "error": "Package 'openai' nicht installiert"}
    validate_openai_chat_jsonl(train_path)
    validate_openai_chat_jsonl(val_path)

    client: Any = _OpenAI_factory(api_key=api_key)

    # Upload Dateien
    with open(train_path, "rb") as tf:
        train_file: Any = client.files.create(file=tf, purpose="fine-tune")
    with open(val_path, "rb") as vf:
        val_file: Any = client.files.create(file=vf, purpose="fine-tune")

    job: Any = client.fine_tuning.jobs.create(
        training_file=train_file.id,
        validation_file=val_file.id,
        model=model,
    )
    return {"ok": True, "job": job.id, "train_file": train_file.id, "val_file": val_file.id}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="OpenAI Fine-Tuning Job starten")
    p.add_argument("train", help="Pfad zu *_train.jsonl (openai_chat)")
    p.add_argument("val", help="Pfad zu *_val.jsonl (openai_chat)")
    p.add_argument("--model", default="gpt-4o-mini")
    p.add_argument("--validate-only", action="store_true", help="Nur JSONL prüfen, keinen Job starten")
    args = p.parse_args()

    if args.validate_only:
        try:
            validate_openai_chat_jsonl(args.train)
            validate_openai_chat_jsonl(args.val)
            print("VALIDATION_OK")
        except Exception as e:
            print("VALIDATION_ERROR:", str(e))
    else:
        out = start_finetune(args.train, args.val, args.model)
        if out.get("ok"):
            print("Job:", out["job"], "TrainFile:", out["train_file"], "ValFile:", out["val_file"])
        else:
            print("Fehler:", out.get("error"))
