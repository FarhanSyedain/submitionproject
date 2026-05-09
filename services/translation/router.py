"""Pick a translator based on settings.TRANSLATION_PROVIDER."""
from __future__ import annotations

from django.conf import settings

from services.translation.base import BaseTranslator


def get_translator(provider: str | None = None) -> BaseTranslator:
    chosen = (provider or settings.TRANSLATION_PROVIDER or "llm").lower()

    if chosen == "local_http":
        from services.translation.local_http_client import LocalHTTPTranslator

        return LocalHTTPTranslator(
            url=settings.TRANSLATION_URL,
            text_field=settings.TRANSLATION_TEXT_FIELD,
            target_field=settings.TRANSLATION_TARGET_FIELD,
            source_field=settings.TRANSLATION_SOURCE_FIELD,
            response_field=settings.TRANSLATION_RESPONSE_FIELD,
        )

    if chosen == "huggingface":
        from services.translation.hf_transformers_client import HFTranslator

        return HFTranslator(
            model_id=settings.HF_TRANSLATION_MODEL,
            max_new_tokens=settings.HF_TRANSLATION_MAX_NEW_TOKENS,
            dtype=settings.HF_TRANSLATION_DTYPE,
        )

    # Default: use whatever LLM client is configured (Gemini / Ollama / Claude).
    from services.llm import get_llm_client
    from services.translation.llm_translator import LLMTranslator

    return LLMTranslator(get_llm_client())
