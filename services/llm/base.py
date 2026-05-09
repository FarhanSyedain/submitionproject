"""Abstract LLM client + JSON parsing helpers shared by all providers."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class CompletionResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0


class BaseLLMClient:
    """Common interface every provider must implement."""

    provider: str = "base"
    model: str = ""

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 2000,
        module: str = "",
    ) -> CompletionResult:
        raise NotImplementedError

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 2000,
        module: str = "",
        retries: int = 1,
    ) -> tuple[dict[str, Any], CompletionResult]:
        """Run `complete` and parse JSON. Retries once with a stricter nudge."""
        last_err: Exception | None = None
        last_result: CompletionResult | None = None
        attempt_user = user
        for attempt in range(retries + 1):
            result = self.complete(
                system=system, user=attempt_user, max_tokens=max_tokens, module=module
            )
            last_result = result
            try:
                return parse_json(result.text), result
            except (json.JSONDecodeError, ValueError) as exc:
                last_err = exc
                attempt_user = (
                    user
                    + "\n\nIMPORTANT: Reply with ONLY a valid JSON object. "
                    "No markdown fences, no commentary, no preamble."
                )
        raise ValueError(
            f"LLM returned non-JSON after {retries + 1} attempts: {last_err}\n"
            f"Last text: {last_result.text[:500] if last_result else '(no result)'}"
        )


_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def parse_json(text: str) -> dict[str, Any]:
    """Tolerant JSON parsing — handles code fences, leading/trailing prose,
    and uses `raw_decode` to peel off the first JSON object even when
    the model appends extra commentary after it (a common Gemini behaviour).
    """
    if not text:
        raise ValueError("Empty LLM response")

    candidate = text.strip()

    # 1) Try as-is.
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # 2) Strip code fences.
    fenced = _FENCE_RE.search(candidate)
    if fenced:
        inner = fenced.group(1).strip()
        try:
            return json.loads(inner)
        except json.JSONDecodeError:
            candidate = inner

    # 3) Use raw_decode from the first '{' so trailing text is ignored.
    start = candidate.find("{")
    if start != -1:
        try:
            obj, _idx = json.JSONDecoder().raw_decode(candidate[start:])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            # Last-resort: try the widest {...} window.
            end = candidate.rfind("}")
            if end > start:
                try:
                    return json.loads(candidate[start : end + 1])
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Could not parse JSON block: {exc}") from exc

    raise ValueError("No JSON object found in response")
