#!/usr/bin/env python
from __future__ import annotations

"""
QLoRA-/SFT-Training (TRL SFTTrainer) für Chat-Daten (openai_chat JSONL).

Hinweise:
- GPU empfohlen; CPU funktioniert für Mini-Tests (sehr langsam).
- Windows: bitsandbytes ist i. d. R. nicht verfügbar; 4-bit nur optional/wo unterstützt.
- Datensatz: openai_chat JSONL mit Struktur { messages: [{role, content}, ...] }.
"""

# pyright: reportUnknownMemberType=false, reportUnknownArgumentType=false, reportUnknownVariableType=false, reportUnknownParameterType=false, reportUnknownLambdaType=false

import argparse
import json
import os
from typing import Any, Dict, List, Set

import torch
from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer
from trl.trainer.sft_config import SFTConfig
from peft import LoraConfig


def _read_openai_chat_jsonl(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
                if isinstance(obj, dict) and isinstance(obj.get("messages"), list):
                    rows.append({"messages": obj["messages"]})
            except Exception:
                continue
    return rows


def load_openai_chat_jsonl(path: str) -> Dataset:
    rows = _read_openai_chat_jsonl(path)
    if not rows:
        raise RuntimeError(f"Keine gültigen Einträge in {path} gefunden")
    return Dataset.from_list(rows)


def format_with_chat_template(examples: Dict[str, Any], tokenizer: Any) -> Dict[str, List[str]]:
    texts: List[str] = []
    for msgs in examples.get("messages", []):
        try:
            text = tokenizer.apply_chat_template(
                msgs,
                tokenize=False,
                add_generation_prompt=False,
            )
        except Exception:
            parts = []
            for m in msgs:
                parts.append(f"{m.get('role')}: {m.get('content')}")
            text = "\n".join(parts)
        texts.append(text)
    return {"text": texts}


def _present_target_modules(model: Any, candidates: List[str]) -> List[str]:
    names: List[str] = list(dict(model.named_modules()).keys())
    def exists(c: str) -> bool:
        for n in names:
            if n.endswith(c) or (f".{c}" in n):
                return True
        return False
    return [c for c in candidates if exists(c)]


def guess_lora_target_modules(model: Any) -> List[str]:
    mt = getattr(getattr(model, "config", object()), "model_type", "") or ""
    mt = str(mt).lower()
    # Common presets
    llama_like = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    gpt2_like = ["c_attn", "c_fc", "c_proj"]
    gptj_like = ["q_proj", "k_proj", "v_proj", "out_proj", "fc_in", "fc_out"]
    neox_like = ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"]

    if any(x in mt for x in ["llama", "mistral", "qwen2", "qwen", "phi"]):
        found = _present_target_modules(model, llama_like)
    elif mt in ("gpt2",):
        found = _present_target_modules(model, gpt2_like)
    elif mt in ("gptj",):
        found = _present_target_modules(model, gptj_like)
    elif mt in ("gpt_neox", "gptneox", "neox"):
        found = _present_target_modules(model, neox_like)
    else:
        # Fallback: try llama-like first, then gpt2-like
        found = _present_target_modules(model, llama_like) or _present_target_modules(model, gpt2_like)
    if not found:
        # As last resort, try any module containing 'proj' or 'attn' or 'fc'
        names: List[str] = list(dict(model.named_modules()).keys())
        heur_set: Set[str] = set()
        for n in names:
            base = n.split(".")[-1]
            if any(k in base for k in ("proj", "attn", "fc", "mlp")):
                heur_set.add(base)
        found = sorted(heur_set)
    if not found:
        raise ValueError(f"Konnte keine passenden target_modules ermitteln für model_type='{mt}'.")
    # Preserve order and unique
    seen: Set[str] = set()
    unique: List[str] = []
    for x in found:
        if x not in seen:
            seen.add(x)
            unique.append(x)
    return unique


def build_lora_config(model: Any, r: int = 16, alpha: int = 32, dropout: float = 0.05) -> LoraConfig:
    targets = guess_lora_target_modules(model)
    mt = str(getattr(getattr(model, "config", object()), "model_type", "")).lower()
    fan_in_fan_out: bool = True if mt == "gpt2" else False
    return LoraConfig(
        r=r,
        lora_alpha=alpha,
        lora_dropout=dropout,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=targets,
        fan_in_fan_out=fan_in_fan_out,
    )


def _has_cuda() -> bool:
    try:
        cuda = getattr(torch, "cuda", None)
        return bool(cuda and getattr(cuda, "is_available", lambda: False)())
    except Exception:
        return False


def main() -> int:
    p = argparse.ArgumentParser(description="QLoRA-Training für openai_chat JSONL")
    p.add_argument("data", help="Pfad zur JSONL (train)")
    p.add_argument("--model", default="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    p.add_argument("--output", default=os.path.join("outputs", "lora-out"))
    p.add_argument("--per-device-train-batch-size", type=int, default=1)
    p.add_argument("--grad-accum", type=int, default=8, help="Gradient Accumulation steps (effektiver Batch auf kleinem VRAM)")
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--max-steps", type=int, default=-1)
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--fp16", action="store_true")
    p.add_argument("--load-in-4bit", action="store_true", help="4bit-Loading aktivieren (erfordert bitsandbytes und passenden Stack)")
    p.add_argument("--max-length", type=int, default=1024)
    # LoRA Hyperparameter explizit überschreibbar
    p.add_argument("--lora-r", type=int, default=int(os.getenv("LORA_R", "8")))
    p.add_argument("--lora-alpha", type=int, default=int(os.getenv("LORA_ALPHA", "16")))
    p.add_argument("--lora-dropout", type=float, default=float(os.getenv("LORA_DROPOUT", "0.05")))
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)

    tokenizer: Any = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    # Für SFT ist rechts-Padding üblich
    try:
        tokenizer.padding_side = "right"
    except Exception:
        pass

    has_cuda = _has_cuda()
    dtype: Any
    if has_cuda and args.fp16:
        dtype = torch.float16
    elif has_cuda and args.bf16:
        dtype = torch.bfloat16
    else:
        dtype = None
    model: Any
    if args.load_in_4bit:
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            torch_dtype=dtype,
            load_in_4bit=True,
            device_map="auto",
        )
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.model,
            torch_dtype=dtype,
            device_map="auto",
        )

    # Sicherstellen, dass pad_token_id gesetzt ist (vermeidet Warnungen bei Padding)
    try:
        if getattr(model.config, "pad_token_id", None) is None and getattr(tokenizer, "pad_token_id", None) is not None:
            model.config.pad_token_id = tokenizer.pad_token_id
    except Exception:
        pass

    ds = load_openai_chat_jsonl(args.data)
    ds = ds.map(
        lambda ex: format_with_chat_template(ex, tokenizer),
        batched=True,
        remove_columns=ds.column_names,  # 'messages' entfernen; es bleibt nur 'text'
    )

    # Trainingsargumente: CPU/GPU dynamisch
    sft_cfg = SFTConfig(
        output_dir=args.output,
        per_device_train_batch_size=max(1, args.per_device_train_batch_size),
        gradient_accumulation_steps=max(1, args.grad_accum),
        num_train_epochs=float(args.epochs),
        max_steps=int(args.max_steps),
        learning_rate=float(args.lr),
        logging_steps=1,
        save_steps=0,
        save_total_limit=1,
        report_to="none",
        bf16=bool(args.bf16) if has_cuda else False,
        fp16=bool(args.fp16) if has_cuda else False,
        use_cpu=not has_cuda,
        dataset_text_field="text",
        max_length=int(args.max_length),
        packing=False,
    )

    # LoRA Hyperparameter (CLI überschreibt ENV)
    r = int(args.lora_r)
    alpha = int(args.lora_alpha)
    dropout = float(args.lora_dropout)
    lora_cfg = build_lora_config(model, r=r, alpha=alpha, dropout=dropout)

    trainer = SFTTrainer(
        model=model,
        args=sft_cfg,
        train_dataset=ds,
        processing_class=tokenizer,
        peft_config=lora_cfg,
    )

    trainer.train()
    # save_pretrained sicher aufrufen (pyright: optional attribute)
    _trained_model: Any = getattr(trainer, "model", None)
    if _trained_model is not None:
        try:
            _trained_model.save_pretrained(args.output)
        except Exception:
            pass
    tokenizer.save_pretrained(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
