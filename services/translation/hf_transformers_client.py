"""Hugging Face Transformers translator for the koshur-kouter ks↔en model.

Uses the chat-template recipe described by the model card:
    Omarrran/koshur-kouter-ks-en_v1

The model + tokenizer are loaded once per process and cached in module
state, so subsequent requests skip the cold-start cost (~10–30s on CPU).

Only en↔ks is supported by this model; calls in any other direction
raise `ValueError`.
"""
from __future__ import annotations

import logging
import re
import threading

from services.translation.base import BaseTranslator

logger = logging.getLogger(__name__)

_MODEL_LOCK = threading.Lock()
_MODEL_CACHE: dict[str, tuple] = {}

DEFAULT_MODEL_ID = "Omarrran/koshur-kouter-ks-en_v1"

# This model is small and trained on short utterances. Splitting on
# sentence-ish boundaries before translating gives much better output
# than feeding it a whole paragraph at once.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z؀-ۿ])")


class HFTranslator(BaseTranslator):
    provider = "huggingface"

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        *,
        max_new_tokens: int = 256,
        dtype: str = "bfloat16",  # bfloat16 | float16 | float32
        device_map: str = "auto",
    ) -> None:
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.dtype = dtype
        self.device_map = device_map

    # ── memory management ────────────────────────────────────────────────
    @classmethod
    def unload_all(cls) -> int:
        """Evict every cached HF translator from process memory.

        Returns the number of models that were evicted. Frees ~2–3 GB per
        small model so a large local LLM (Ollama qwen3:30b etc.) has room
        to load. Safe to call when nothing is loaded — it's a no-op.
        """
        import gc

        with _MODEL_LOCK:
            evicted = len(_MODEL_CACHE)
            _MODEL_CACHE.clear()
        gc.collect()

        try:
            import torch

            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        return evicted

    # ── lazy model load (cached per-process) ────────────────────────────
    def _get_model(self):
        cache_key = f"{self.model_id}:{self.dtype}"
        with _MODEL_LOCK:
            if cache_key in _MODEL_CACHE:
                return _MODEL_CACHE[cache_key]

            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            torch_dtype = getattr(torch, self.dtype, torch.float32)
            logger.info("Loading HF translator %s (dtype=%s)", self.model_id, self.dtype)

            tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            try:
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_id,
                    torch_dtype=torch_dtype,
                    device_map=self.device_map,
                ).eval()
            except (RuntimeError, NotImplementedError) as exc:
                # Fallback for hardware that doesn't support bfloat16 (e.g. M1).
                logger.warning(
                    "%s load failed at dtype=%s (%s); retrying float32",
                    self.model_id, self.dtype, exc,
                )
                model = AutoModelForCausalLM.from_pretrained(
                    self.model_id,
                    torch_dtype=torch.float32,
                    device_map=self.device_map,
                ).eval()
            _MODEL_CACHE[cache_key] = (tokenizer, model)
            return tokenizer, model

    # ── BaseTranslator ───────────────────────────────────────────────────
    def translate(
        self, text: str, *, target_lang: str = "ks", source_lang: str = "en"
    ) -> str:
        if not text.strip():
            return ""

        direction = self._direction(source_lang, target_lang)

        # Split long input into sentence-sized chunks so each generate()
        # call has plenty of headroom inside max_new_tokens.
        chunks = _split_into_chunks(text, max_chars=240)
        translated = [self._translate_chunk(c, direction) for c in chunks]
        return " ".join(t for t in translated if t)

    # ── helpers ──────────────────────────────────────────────────────────
    @staticmethod
    def _direction(source_lang: str, target_lang: str) -> str:
        pair = (source_lang.lower(), target_lang.lower())
        if pair == ("en", "ks"):
            return "en2ks"
        if pair == ("ks", "en"):
            return "ks2en"
        raise ValueError(
            f"koshur-kouter only supports en↔ks; got {source_lang}→{target_lang}"
        )

    def _translate_chunk(self, source: str, direction: str) -> str:
        if not source.strip():
            return ""

        import torch  # local import keeps non-HF deployments lightweight

        tokenizer, model = self._get_model()

        instructions = {
            "ks2en": "Translate the text below to English. Return only the translation.",
            "en2ks": "Translate the text below to Kashmiri. Return only the translation.",
        }
        messages = [
            {"role": "system", "content": instructions[direction]},
            {"role": "user", "content": source},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = tokenizer(
            prompt, return_tensors="pt", truncation=True, max_length=1024
        ).to(model.device)

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=self.max_new_tokens,
                do_sample=False,
                repetition_penalty=1.15,
                no_repeat_ngram_size=3,
                pad_token_id=tokenizer.eos_token_id,
            )

        suffix = outputs[0][inputs.input_ids.shape[1]:]
        decoded = tokenizer.decode(suffix, skip_special_tokens=True)
        return _first_nonempty_line(decoded)


# ── module-level helpers ────────────────────────────────────────────────
def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return text.strip()


def _split_into_chunks(text: str, *, max_chars: int = 240) -> list[str]:
    """Split text into sentence-aware chunks no longer than ~max_chars."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    sentences = _SENTENCE_SPLIT.split(text)
    chunks: list[str] = []
    buffer = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if not buffer:
            buffer = sentence
        elif len(buffer) + 1 + len(sentence) <= max_chars:
            buffer = f"{buffer} {sentence}"
        else:
            chunks.append(buffer)
            buffer = sentence
    if buffer:
        chunks.append(buffer)

    # Sentence split may still leave huge chunks (e.g. one long sentence).
    # Hard-wrap anything still over budget so generate() can keep up.
    out: list[str] = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            out.append(chunk)
            continue
        for i in range(0, len(chunk), max_chars):
            out.append(chunk[i : i + max_chars])
    return out
