"""Customer feedback analyzer.

Differs from the other agents: it processes a specific FeedbackSubmission
(usually triggered when the user pastes feedback) rather than running as
part of the main pipeline.
"""
from __future__ import annotations

from apps.feedback.models import FeedbackInsight, FeedbackSubmission

from services.llm.base import BaseLLMClient
from services.modules.base import BaseAgent


class FeedbackAgent(BaseAgent):
    module = "feedback"
    system_prompt = (
        "You are a product analyst. Analyze the customer feedback below and "
        "extract structured insights. Return ONLY valid JSON:\n"
        "{\n"
        '  "insights": [\n'
        "    {\n"
        '      "insight_type": "pain_point|feature_request|compliment|bug|question",\n'
        '      "title": "...",\n'
        '      "description": "...",\n'
        '      "frequency_score": 1,\n'
        '      "sentiment": "positive|neutral|negative",\n'
        '      "priority": "low|medium|high|critical",\n'
        '      "example_quotes": ["..."]\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "frequency_score is an integer 1–10."
    )

    def __init__(self, submission: FeedbackSubmission, client: BaseLLMClient) -> None:
        super().__init__(submission.session, client)
        self.submission = submission

    def build_user_prompt(self) -> str:
        return (
            f"{self._business_context()}\n\n"
            f"Customer feedback to analyze:\n---\n{self.submission.raw_text}\n---"
        )

    def parse_and_save(self, payload: dict) -> None:
        for item in payload.get("insights", []):
            FeedbackInsight.objects.create(
                submission=self.submission,
                insight_type=item.get("insight_type", "pain_point") or "pain_point",
                title=str(item.get("title", "Untitled insight"))[:255],
                description=item.get("description", "") or "",
                frequency_score=int(item.get("frequency_score", 1) or 1),
                sentiment=item.get("sentiment", "neutral") or "neutral",
                priority=item.get("priority", "medium") or "medium",
                example_quotes=item.get("example_quotes") or [],
            )
