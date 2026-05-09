"""Generic HTTP translator. Point it at any local translation service.

Default contract (override via .env if your service differs):

    POST {TRANSLATION_URL}
    Content-Type: application/json
    Body: {"text": "...", "target_lang": "ks", "source_lang": "en"}

    Response: {"translation": "..."}        ← key configurable

If your local server uses a different request shape, the simplest fix is
to put a thin proxy in front of it. Otherwise, edit the four constants
at the top of `LocalHTTPTranslator.translate`.
"""
from __future__ import annotations

import requests

from services.translation.base import BaseTranslator


class LocalHTTPTranslator(BaseTranslator):
    provider = "local_http"

    def __init__(
        self,
        url: str,
        *,
        timeout: int = 60,
        text_field: str = "text",
        target_field: str = "target_lang",
        source_field: str = "source_lang",
        response_field: str = "translation",
        extra_payload: dict | None = None,
    ) -> None:
        if not url:
            raise ValueError("TRANSLATION_URL is required for LocalHTTPTranslator")
        self.url = url
        self.timeout = timeout
        self.text_field = text_field
        self.target_field = target_field
        self.source_field = source_field
        self.response_field = response_field
        self.extra_payload = extra_payload or {}

    def translate(
        self, text: str, *, target_lang: str = "ks", source_lang: str = "en"
    ) -> str:
        if not text.strip():
            return ""

        payload = {
            self.text_field: text,
            self.target_field: target_lang,
            self.source_field: source_lang,
            **self.extra_payload,
        }
        response = requests.post(self.url, json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        # Walk a dotted path into the response (e.g. "data.translation").
        out = data
        for part in self.response_field.split("."):
            if not isinstance(out, dict):
                break
            out = out.get(part, "")
        return str(out or "").strip()
