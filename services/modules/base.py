"""Base class for all analysis agents.

Each agent owns one stage of the Zeaniv pipeline. Subclasses implement
`build_user_prompt` (what to ask the LLM) and `parse_and_save` (how to
persist the structured response). The base class handles status updates,
LLM logging, and token accounting so individual agents stay focused.
"""
from __future__ import annotations

from typing import ClassVar

from django.db.models import F

from services.llm.base import BaseLLMClient, CompletionResult


class BaseAgent:
    module: ClassVar[str] = ""
    system_prompt: ClassVar[str] = ""
    # Per-agent token budget. Override in subclasses that produce long output
    # (ideation, validation, report) — defaults are sized for short outputs.
    max_tokens: ClassVar[int] = 2000

    def __init__(self, session, client: BaseLLMClient) -> None:
        self.session = session
        self.client = client

    @property
    def business(self):
        return self.session.business

    # ── subclass hooks ───────────────────────────────────────────────────
    def build_user_prompt(self) -> str:
        raise NotImplementedError

    def parse_and_save(self, payload: dict) -> None:
        raise NotImplementedError

    # ── runner ───────────────────────────────────────────────────────────
    def run(self) -> None:
        self._update_status("running")
        result: CompletionResult | None = None
        try:
            user_prompt = self.build_user_prompt()
            payload, result = self.client.complete_json(
                system=self.system_prompt,
                user=user_prompt,
                max_tokens=self.max_tokens,
                module=self.module,
            )
            self.parse_and_save(payload)
        except Exception as exc:
            self._update_status("failed")
            self._log(result, success=False, error=str(exc))
            raise
        self._update_status("completed")
        self._log(result, success=True, error="")

    # ── helpers ──────────────────────────────────────────────────────────
    def _update_status(self, status: str) -> None:
        statuses = dict(self.session.module_status or {})
        statuses[self.module] = status
        self.session.module_status = statuses
        self.session.save(update_fields=["module_status"])

    def _log(self, result: CompletionResult | None, success: bool, error: str) -> None:
        from apps.analysis.models import AnalysisSession, LlmLog

        LlmLog.objects.create(
            session=self.session,
            provider=self.client.provider,
            model=self.client.model,
            module=self.module,
            prompt_tokens=result.prompt_tokens if result else 0,
            completion_tokens=result.completion_tokens if result else 0,
            latency_ms=result.latency_ms if result else None,
            success=success,
            error=error or "",
        )
        if result:
            tokens = (result.prompt_tokens or 0) + (result.completion_tokens or 0)
            if tokens:
                AnalysisSession.objects.filter(pk=self.session.pk).update(
                    total_tokens=F("total_tokens") + tokens
                )

    # ── shared context ──────────────────────────────────────────────────
    def _business_context(self) -> str:
        b = self.business
        parts = [
            f"Business name: {b.name}",
            f"Description: {b.description}",
        ]
        if b.industry:
            parts.append(f"Industry: {b.industry}")
        if b.target_market:
            parts.append(f"Target market: {b.target_market}")
        if b.location:
            parts.append(f"Location: {b.location}")
        if b.stage:
            parts.append(f"Stage: {b.stage}")
        return "\n".join(parts)
