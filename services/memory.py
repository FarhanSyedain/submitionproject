"""Model-swap orchestration for memory-constrained machines.

When you run a heavyweight local LLM (Ollama qwen3:30b ≈ 18GB) AND a local
HF translator (koshur-kouter ≈ 2.5GB), holding both in memory simultaneously
chews through 20+ GB. Most consumer machines can't sustain that.

This module exposes two entry points:

    unload_translator()  → evicts cached HF translator weights from this
                            Python process, returns memory to the OS.

    unload_llm()         → tells the *external* LLM service (e.g. Ollama)
                            to release its weights via `keep_alive: 0`.
                            Cloud LLMs (Gemini, Claude) are no-ops.

Behaviour is gated by `settings.ENABLE_MODEL_SWAP` so you can turn the
whole thing off on a high-RAM box where keeping both loaded is faster.
"""
from __future__ import annotations

import logging

from django.conf import settings

logger = logging.getLogger(__name__)


def unload_translator() -> None:
    """Evict any cached HF translator model from this process."""
    if not _swap_enabled():
        return
    try:
        from services.translation.hf_transformers_client import HFTranslator

        evicted = HFTranslator.unload_all()
        if evicted:
            logger.info("Unloaded %d HF translator model(s) from memory", evicted)
    except Exception as exc:  # noqa: BLE001 — never block on best-effort cleanup
        logger.warning("unload_translator failed: %s", exc)


def unload_llm() -> None:
    """Ask the configured LLM provider to release its weights.

    Only the Ollama backend can actually unload — cloud APIs are no-ops.
    """
    if not _swap_enabled():
        return

    provider = (getattr(settings, "LLM_PROVIDER", "") or "").lower()
    if provider != "ollama":
        return  # cloud / mock providers don't hold local weights

    try:
        import requests

        # `keep_alive: 0` tells Ollama to unload the model immediately
        # after handling this (empty) request.
        response = requests.post(
            f"{settings.OLLAMA_BASE_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "keep_alive": 0,
            },
            timeout=10,
        )
        if response.ok:
            logger.info(
                "Asked Ollama to unload %s (keep_alive=0)", settings.OLLAMA_MODEL
            )
        else:
            logger.warning(
                "Ollama unload returned %s: %s",
                response.status_code,
                response.text[:200],
            )
    except Exception as exc:  # noqa: BLE001
        logger.warning("unload_llm (ollama) failed: %s", exc)


def swap_to(target: str) -> None:
    """Convenience: free the *other* service's memory before using `target`.

    target ∈ {"llm", "translation"}.
    """
    if target == "llm":
        unload_translator()
    elif target == "translation":
        unload_llm()
    else:
        raise ValueError(f"swap_to: target must be 'llm' or 'translation', got {target!r}")


def _swap_enabled() -> bool:
    return bool(getattr(settings, "ENABLE_MODEL_SWAP", True))
