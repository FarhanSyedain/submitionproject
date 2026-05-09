"""Ollama (local Llama / Mistral / etc.) client.

Hits Ollama's /api/chat endpoint with `format: "json"` so the model is
encouraged to return parseable JSON.
"""
from __future__ import annotations

import time

import requests

from services.llm.base import BaseLLMClient, CompletionResult


class OllamaClient(BaseLLMClient):
    provider = "ollama"

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2",
        timeout: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 2000,
        module: str = "",
    ) -> CompletionResult:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
            "format": "json",
            "options": {"num_predict": max_tokens},
        }

        start = time.perf_counter()
        response = requests.post(url, json=payload, timeout=self.timeout)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        response.raise_for_status()
        data = response.json()

        text = data.get("message", {}).get("content", "") or ""
        return CompletionResult(
            text=text,
            prompt_tokens=int(data.get("prompt_eval_count", 0) or 0),
            completion_tokens=int(data.get("eval_count", 0) or 0),
            latency_ms=elapsed_ms,
        )
