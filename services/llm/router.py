"""Picks an LLM client based on settings.LLM_PROVIDER."""
from __future__ import annotations

from django.conf import settings

from services.llm.base import BaseLLMClient


def get_llm_client(provider: str | None = None) -> BaseLLMClient:
    """Return a client for the requested provider (or the configured default)."""
    chosen = (provider or settings.LLM_PROVIDER or "mock").lower()

    if chosen == "ollama":
        from services.llm.ollama_client import OllamaClient

        return OllamaClient(
            base_url=settings.OLLAMA_BASE_URL,
            model=settings.OLLAMA_MODEL,
        )

    if chosen == "gemini":
        from services.llm.gemini_client import GeminiClient

        return GeminiClient(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_MODEL,
        )

    # Default: mock — safe, free, deterministic.
    from services.llm.mock_client import MockClient

    return MockClient()
