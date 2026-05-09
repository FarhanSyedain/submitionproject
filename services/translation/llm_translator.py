"""Translator that delegates to whatever BaseLLMClient is configured.

Useful as a sensible default — works against Gemini, Claude, Ollama, or
any other backend the project already supports, with no extra services
to run.

`translate_many` batches all strings into a single LLM call, which is
critical for staying under per-minute rate limits on free tiers.
"""
from __future__ import annotations

import json

from services.llm import BaseLLMClient
from services.translation.base import LANGUAGES, BaseTranslator


class LLMTranslator(BaseTranslator):
    provider = "llm"

    def __init__(self, client: BaseLLMClient) -> None:
        self.client = client

    def translate(
        self, text: str, *, target_lang: str = "ks", source_lang: str = "en"
    ) -> str:
        if not text.strip():
            return ""

        target_meta = LANGUAGES.get(target_lang, {})
        source_meta = LANGUAGES.get(source_lang, {})
        target_name = target_meta.get("name", target_lang)
        source_name = source_meta.get("name", source_lang)
        script_hint = target_meta.get("script_instruction", "")

        # Use complete_json to stay compatible with providers that force a
        # JSON response (e.g. Gemini with response_mime_type=application/json).
        system = (
            f"You are a professional {source_name}-to-{target_name} translator. "
            "Translate the user's text faithfully. Return ONLY this JSON:\n"
            '{ "translation": "..." }\n'
            "Preserve names, numbers, URLs, and code verbatim. "
            f"{script_hint}"
        )
        data, _ = self.client.complete_json(
            system=system,
            user=text,
            max_tokens=max(800, int(len(text) * 3)),
            module="translate",
        )
        return (data.get("translation") or "").strip()

    def translate_many(
        self,
        texts: list[str],
        *,
        target_lang: str = "ks",
        source_lang: str = "en",
    ) -> list[str]:
        """Batch all strings into one LLM call.

        Returns a list of the same length as `texts`, preserving order.
        Empty/whitespace inputs round-trip as empty strings.
        """
        if not texts:
            return []

        # Build the index → text map for non-empty strings, so we don't
        # waste tokens translating empty placeholders.
        items = [(i, t) for i, t in enumerate(texts) if t.strip()]
        if not items:
            return ["" for _ in texts]

        target_meta = LANGUAGES.get(target_lang, {})
        source_meta = LANGUAGES.get(source_lang, {})
        target_name = target_meta.get("name", target_lang)
        source_name = source_meta.get("name", source_lang)
        script_hint = target_meta.get("script_instruction", "")

        system = (
            f"You are a professional {source_name}-to-{target_name} translator. "
            "You receive a JSON object with an `inputs` array of strings. "
            "Translate every entry faithfully and return ONLY this JSON:\n"
            '{ "translations": ["...", "..."] }\n'
            "The output array MUST be the same length as the input array, "
            "in the same order. Preserve names, numbers, URLs, and code "
            "verbatim. No explanations, no preamble. "
            f"{script_hint}"
        )
        user = json.dumps(
            {"inputs": [t for _, t in items]}, ensure_ascii=False
        )
        # Headroom: translation often inflates Kashmiri script vs ASCII.
        budget = max(2000, sum(len(t) for _, t in items) * 4)

        data, _ = self.client.complete_json(
            system=system, user=user, max_tokens=budget, module="translate"
        )
        translations = data.get("translations") or []

        # Stitch back into the original-length list.
        out = ["" for _ in texts]
        for (orig_idx, _orig_text), translated in zip(items, translations):
            out[orig_idx] = (
                (translated or "").strip()
                if isinstance(translated, str)
                else ""
            )
        return out
