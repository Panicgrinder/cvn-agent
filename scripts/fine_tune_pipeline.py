#!/usr/bin/env python
"""
Mini-Pipeline für LoRA-Fine-Tuning:
- Wählt die neueste kuratierte Train-Datei (finetune_*_train.jsonl) oder nimmt --train-file
- Führt scripts/train_lora.py mit den übergebenen Hyperparametern aus
- Führt vorab Environment-Checks durch (optionale Abkürzung via --no-check)

Hinweise:
- Für GPU-Training werden zusätzliche Pakete benötigt (siehe requirements-train.txt) und eine passende Torch-Installation.
- Unter Windows wird WSL2 oder Linux empfohlen.
"""
from __future__ import annotations

import argparse
import glob
import os
import sys
from typing import Optional, List
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Kuratierte Liste kostenloser/offener Modelle, die ohne Gate nutzbar sind
FREE_MODEL_ALLOWLIST: List[str] = [
    "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
    "Qwen/Qwen2.5-0.5B-Instruct",
    "Qwen/Qwen2.5-1.5B-Instruct",
    "sshleifer/tiny-gpt2",
    "gpt2",
]


def latest_train_file(dir_path: str) -> Optional[str]:
    files: List[str] = sorted(glob.glob(os.path.join(dir_path, "finetune_*_train.jsonl")), reverse=True)
    return files[0] if files else None


def env_check() -> Optional[str]:
    """Rudimentärer Check für Trainingsumgebung; gibt None bei OK zurück, sonst Fehlermeldung."""
    try:
        import torch  # type: ignore
    except Exception:
        return "torch nicht importierbar; bitte PyTorch GPU/CPU gemäß Hardware installieren."
    try:
        import transformers  # type: ignore
        import datasets  # type: ignore
        import peft  # type: ignore
        import trl  # type: ignore
    except Exception as e:
        return f"Trainingsabhängigkeiten fehlen: {e} (pip -r requirements-train.txt)"
    # Optional GPU-Hinweis
    try:
        if hasattr(torch, "cuda") and torch.cuda.is_available():  # type: ignore[attr-defined]
            return None
        return "CUDA nicht verfügbar; Training läuft vermutlich sehr langsam auf CPU."
    except Exception:
        return None


def main() -> int:
    p = argparse.ArgumentParser(description="Mini-Pipeline für LoRA Fine-Tuning")
    p.add_argument("--finetune-dir", default=os.path.join("eval", "results", "finetune"))
    p.add_argument("--train-file", default=None, help="Konkrete finetune_*_train.jsonl übergeben")
    p.add_argument("--model", default="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    p.add_argument("--output", default=None, help="Ausgabeverzeichnis für Adapter; Standard: outputs/lora-<ts>")
    p.add_argument("--per-device-train-batch-size", type=int, default=1)
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--max-steps", type=int, default=-1)
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--no-check", action="store_true", help="Umgebungs-Checks überspringen")
    p.add_argument("--only-free", action="store_true", default=True, help="Nur kostenlose/ungated Modelle erlauben")
    args = p.parse_args()

    train_file = args.train_file or latest_train_file(args.finetune_dir)
    if not train_file or not os.path.exists(train_file):
        print({"ok": False, "error": f"Keine Train-Datei gefunden in {args.finetune_dir}"})
        return 2

    from utils.time_utils import now_compact
    out_dir = args.output or os.path.join("outputs", f"lora-{now_compact()}")
    os.makedirs(out_dir, exist_ok=True)

    # Optionaler Free-Model-Guard
    if args.only_free and args.model not in FREE_MODEL_ALLOWLIST:
        print({
            "ok": False,
            "error": f"Modell '{args.model}' ist nicht in der Free-Allowlist.",
            "allowed": FREE_MODEL_ALLOWLIST,
            "hint": "Nutze --only-free false, um andere Modelle explizit zu erlauben.",
        })
        return 4

    if not args.no_check:
        msg = env_check()
        if msg:
            print({"env_warning": msg})
            # Bei harten fehlenden Abhängigkeiten abbrechen
            if ("nicht importierbar" in msg) or ("fehlen" in msg):
                print({"ok": False, "error": "Trainingsumgebung unvollständig. Siehe requirements-train.txt und PyTorch-Installationshinweise."})
                return 3

    cmd: List[str] = [
        sys.executable,
        os.path.join(PROJECT_ROOT, "scripts", "train_lora.py"),
        train_file,
        "--model", args.model,
        "--output", out_dir,
        "--per-device-train-batch-size", str(args.per_device_train_batch_size),
        "--epochs", str(args.epochs),
        "--lr", str(args.lr),
        "--max-steps", str(args.max_steps),
    ]
    if args.bf16:
        cmd.append("--bf16")
    if args.fp16:
        cmd.append("--fp16")

    print({"running": cmd})
    try:
        # Übergibt stdout/stderr direkt
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
