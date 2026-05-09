"""Exploratory probe: can the koshur-kouter HF model handle general tasks?

The model is trained for ks↔en translation, but it's a CausalLM with a chat
template. We swap in different system prompts to see whether it follows
generic instructions (Q&A, JSON output, structured analysis, code).

Result of this probe drives the question: should we expose it as an LLM
provider in `services.llm.router`, or keep it translation-only?

Run:  python scripts/probe_koshur_kouter_general.py
"""
from __future__ import annotations

import os
import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
warnings.filterwarnings("ignore")

import django  # noqa: E402

django.setup()

import torch  # noqa: E402
from transformers import AutoModelForCausalLM, AutoTokenizer  # noqa: E402

MODEL_ID = "Omarrran/koshur-kouter-ks-en_v1"

PROBES = [
    {
        "label": "[1] General Q&A",
        "system": "You are a helpful assistant. Answer the question concisely.",
        "user": "What is the capital of France?",
        "max_new_tokens": 64,
    },
    {
        "label": "[2] Reasoning / arithmetic",
        "system": "You are a math tutor. Answer concisely.",
        "user": "If A = 2 and B = 3, what is A + B?",
        "max_new_tokens": 32,
    },
    {
        "label": "[3] List output",
        "system": "Return a numbered list. No preamble.",
        "user": "List 3 benefits of regular exercise.",
        "max_new_tokens": 128,
    },
    {
        "label": "[4] JSON output",
        "system": (
            "Return ONLY valid JSON matching this schema:\n"
            '{"name": "...", "age": 0, "city": "..."}\n'
            "No preamble."
        ),
        "user": "Return a JSON profile for someone named Alice, age 30, in Paris.",
        "max_new_tokens": 96,
    },
    {
        "label": "[5] Business-analyst prompt (the kind we use in agents)",
        "system": (
            "You are a business intelligence analyst. Identify 2 competitors "
            "for the business below. Return ONLY JSON:\n"
            '{"competitors": [{"name": "...", "description": "..."}]}'
        ),
        "user": "Business: AI-native business intelligence platform for solo founders.",
        "max_new_tokens": 256,
    },
    {
        "label": "[6] Sanity check — actual translation (en→ks)",
        "system": "Translate the text below to Kashmiri. Return only the translation.",
        "user": "The capital of France is Paris.",
        "max_new_tokens": 96,
    },
    {
        "label": "[7] Code generation",
        "system": "Write only Python code. No markdown, no commentary.",
        "user": "Write a function that returns the factorial of n.",
        "max_new_tokens": 160,
    },
]


def main() -> None:
    print(f"Loading {MODEL_ID}…")
    start = time.perf_counter()
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    ).eval()
    print(f"Loaded in {time.perf_counter() - start:.1f}s on {model.device}\n")

    for probe in PROBES:
        print("=" * 70)
        print(probe["label"])
        print(f"  system: {probe['system'][:80]}")
        print(f"  user:   {probe['user']}")

        messages = [
            {"role": "system", "content": probe["system"]},
            {"role": "user", "content": probe["user"]},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=1024
        ).to(model.device)

        t0 = time.perf_counter()
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=probe["max_new_tokens"],
                do_sample=False,
                repetition_penalty=1.15,
                no_repeat_ngram_size=3,
                pad_token_id=tokenizer.eos_token_id,
            )
        elapsed = time.perf_counter() - t0

        suffix = outputs[0][inputs.input_ids.shape[1]:]
        text = tokenizer.decode(suffix, skip_special_tokens=True).strip()
        print(f"  output ({elapsed:.1f}s, {len(text)} chars):")
        for line in text.splitlines()[:8]:
            print(f"    {line}")
        if len(text.splitlines()) > 8:
            print(f"    … ({len(text.splitlines())} total lines)")
        print()


if __name__ == "__main__":
    main()
