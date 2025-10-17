#!/usr/bin/env python
"""
Erstellt aus einem exportierten Finetuning-Datensatz (openai_chat/alpaca) ein Train/Val-Paket.

Features:
- Shuffle + Repro Seed
- Split (train_ratio)
- Minimal-Längenfilter (Output)
- Dedupe nach Instruction (openai_chat: erste user-Nachricht; alpaca: instruction)
"""
from __future__ import annotations

import os
import json
import random
from typing import Any, Dict, List, Optional, cast
import re


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
                if isinstance(raw, dict):
                    obj: Dict[str, Any] = cast(Dict[str, Any], raw)
                    rows.append(obj)
            except json.JSONDecodeError:
                continue
    return rows


def _write_jsonl(path: str, rows: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _first_user_message(messages: List[Dict[str, str]]) -> str:
    for m in messages:
        if m.get("role") == "user":
            return m.get("content", "")
    return messages[0].get("content", "") if messages else ""


def _output_text(rec: Dict[str, Any], format: str) -> str:
    if format == "alpaca":
        return str(rec.get("output", ""))
    if format == "openai_chat":
        msgs: List[Dict[str, str]] = list(rec.get("messages") or [])
        last = msgs[-1] if msgs else {}
        return str(last.get("content", ""))
    return ""


def _instr_key(rec: Dict[str, Any], format: str) -> str:
    if format == "alpaca":
        return str(rec.get("instruction", ""))
    if format == "openai_chat":
        msgs: List[Dict[str, str]] = list(rec.get("messages") or [])
        return _first_user_message(msgs)
    return ""


def prepare_pack(
    src_path: str,
    out_dir: Optional[str] = None,
    format: str = "openai_chat",
    train_ratio: float = 0.9,
    seed: int = 42,
    min_output_chars: int = 20,
    dedupe_by_instruction: bool = True,
    near_dup_threshold: float = 0.0,
) -> Dict[str, Any]:
    if out_dir is None:
        out_dir = os.path.dirname(src_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    rows = _read_jsonl(src_path)
    if not rows:
        return {"ok": False, "error": "Leere oder ungültige Quelle"}

    # Filter auf minimale Output-Länge
    rows = [r for r in rows if len(_output_text(r, format)) >= min_output_chars]

    # Dedupe Instruction
    if dedupe_by_instruction:
        seen: set[str] = set()
        uniq: List[Dict[str, Any]] = []
        for r in rows:
            key = _instr_key(r, format)
            if key and key not in seen:
                seen.add(key)
                uniq.append(r)
        rows = uniq

    # Optionale Near-Duplicate-Reduktion (einfacher Token-Jaccard auf Instruction)
    def _tok_set(s: str) -> set[str]:
        toks = re.findall(r"\w+", s.lower())
        return set(toks)
    if near_dup_threshold and near_dup_threshold > 0.0:
        kept: List[Dict[str, Any]] = []
        seen_instr: List[set[str]] = []
        for r in rows:
            instr = _instr_key(r, format)
            ts = _tok_set(instr)
            is_dup = False
            for prev in seen_instr:
                inter = len(ts & prev)
                union = len(ts | prev) or 1
                j = inter / union
                if j >= near_dup_threshold:
                    is_dup = True
                    break
            if not is_dup:
                kept.append(r)
                seen_instr.append(ts)
        rows = kept

    if not rows:
        return {"ok": False, "error": "Alle Einträge wurden gefiltert"}

    # Shuffle + Split
    random.Random(seed).shuffle(rows)
    n = len(rows)
    cut = int(n * train_ratio)
    train = rows[:cut]
    val = rows[cut:]

    base = os.path.splitext(os.path.basename(src_path))[0]
    out_train = os.path.join(out_dir, f"{base}_train.jsonl")
    out_val = os.path.join(out_dir, f"{base}_val.jsonl")
    _write_jsonl(out_train, train)
    _write_jsonl(out_val, val)

    return {
        "ok": True,
        "train": out_train,
        "val": out_val,
        "counts": {"train": len(train), "val": len(val), "total": n},
    }


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Train/Val-Split für Finetune-Datensatz")
    p.add_argument("src", help="Pfad zum exportierten JSONL (openai_chat/alpaca)")
    p.add_argument("--format", choices=["openai_chat", "alpaca"], default="openai_chat")
    p.add_argument("--train-ratio", type=float, default=0.9)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--min-output-chars", type=int, default=20)
    p.add_argument("--no-dedupe", action="store_true")
    p.add_argument("--near-dup-threshold", type=float, default=0.0, help="Optional: [0.0–1.0] Token-Jaccard-Schwelle für Near-Dedupe (z. B. 0.8)")
    args = p.parse_args()

    res = prepare_pack(
        args.src,
        format=args.format,
        train_ratio=args.train_ratio,
        seed=args.seed,
        min_output_chars=args.min_output_chars,
        dedupe_by_instruction=(not args.no_dedupe),
        near_dup_threshold=float(args.near_dup_threshold),
    )
    if res.get("ok"):
        print("Train:", res["train"], "Val:", res["val"], "Counts:", res["counts"])
    else:
        print("Fehler:", res.get("error"))
