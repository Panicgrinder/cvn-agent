#!/usr/bin/env python
"""
QLoRA-Training (TRL SFTTrainer) für Chat-Daten (openai_chat JSONL).

Hinweis:
- Erfordert GPU (CUDA) und passende PyTorch-Version.
- Basis-Modell (HF) muss zugänglich sein (z. B. Meta-Llama-3.1-Instruct – Lizenz akzeptieren).
- Windows: Training läuft am besten unter WSL2 oder Linux. BitsAndBytes auf Windows ist eingeschränkt.

Datensatz: openai_chat JSONL mit Struktur { messages: [{role, content}, ...] }.
"""
from __future__ import annotations

import os
import json
from typing import Any, Dict, List
import torch

from datasets import Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer
from peft import LoraConfig
from transformers import TrainingArguments


def load_openai_chat_jsonl(path: str) -> Dataset:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and "messages" in obj:
                rows.append(obj)
    return Dataset.from_list(rows)


def format_with_chat_template(examples, tokenizer):
    texts = []
    for msgs in examples["messages"]:
        try:
            text = tokenizer.apply_chat_template(msgs, tokenize=False, add_generation_prompt=False)
        except Exception:
            # Fallback: simple concat
            text = "\n".join([f"{m.get('role')}: {m.get('content','')}" for m in msgs])
        texts.append(text)
    return {"text": texts}


def main():
    import argparse
    p = argparse.ArgumentParser(description="QLoRA-Training für openai_chat JSONL")
    p.add_argument("data", help="Pfad zur JSONL (train)")
    p.add_argument("--model", default="meta-llama/Meta-Llama-3.1-8B-Instruct")
    p.add_argument("--output", default="./outputs/lora-llama31")
    p.add_argument("--per-device-train-batch-size", type=int, default=1)
    p.add_argument("--epochs", type=int, default=1)
    p.add_argument("--lr", type=float, default=2e-4)
    p.add_argument("--max-steps", type=int, default=-1)
    p.add_argument("--bf16", action="store_true")
    p.add_argument("--load-in-4bit", action="store_true", help="4bit-Loading aktivieren (erfordert bitsandbytes; auf Windows evtl. nicht unterstützt)")
    args = p.parse_args()

    os.makedirs(args.output, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.bfloat16 if args.bf16 else None
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

    ds = load_openai_chat_jsonl(args.data)
    ds = ds.map(lambda ex: format_with_chat_template(ex, tokenizer), batched=True)

    lora = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        bias="none",
        task_type="CAUSAL_LM",
    )

    training_args = TrainingArguments(
        output_dir=args.output,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.per_device_train_batch_size,
        gradient_accumulation_steps=8,
        learning_rate=args.lr,
        logging_steps=10,
        save_steps=200,
        save_total_limit=2,
        bf16=args.bf16,
        report_to=[],
        max_steps=(args.max_steps if args.max_steps and args.max_steps > 0 else None),
    )

    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        peft_config=lora,
        train_dataset=ds,
        dataset_text_field="text",
        max_seq_length=2048,
        args=training_args,
    )

    trainer.train()
    trainer.save_model(args.output)
    tokenizer.save_pretrained(args.output)
    print(f"Saved adapter to {args.output}")


if __name__ == "__main__":
    main()
