"""Google Gemini client using the official `google-genai` SDK.

Free tier on Google AI Studio is generous (~15 RPM / 1M tokens / day on
`gemini-2.5-flash`), which is plenty for hackathon use. Get a key at
https://aistudio.google.com/.
"""
from __future__ import annotations

import time

from services.llm.base import BaseLLMClient, CompletionResult


class GeminiClient(BaseLLMClient):
    provider = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required for the Gemini client")
        # Lazy-import the SDK so the rest of the app loads even if it's missing.
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._genai = genai
        self.model = model

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 2000,
        module: str = "",
    ) -> CompletionResult:
        from google.genai import types

        # Gemini 2.5+ models do "thinking" before responding, and those
        # tokens count toward `max_output_tokens` — which silently truncates
        # JSON responses if you don't disable it. We don't need a chain of
        # thought for our schema-driven tasks.
        config_kwargs = dict(
            system_instruction=system,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
        )
        try:
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
        except (AttributeError, TypeError):  # pragma: no cover — older SDKs
            pass
        config = types.GenerateContentConfig(**config_kwargs)

        start = time.perf_counter()
        response = self._client.models.generate_content(
            model=self.model,
            contents=user,
            config=config,
        )
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        text = response.text or ""
        usage = getattr(response, "usage_metadata", None)
        return CompletionResult(
            text=text,
            prompt_tokens=getattr(usage, "prompt_token_count", 0) if usage else 0,
            completion_tokens=getattr(usage, "candidates_token_count", 0) if usage else 0,
            latency_ms=elapsed_ms,
        )
