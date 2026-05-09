"""Idea validation agent. Scores each idea and writes IdeaValidation rows."""
from __future__ import annotations

import json
from decimal import Decimal

from apps.ideas.models import Idea, IdeaValidation

from services.modules.base import BaseAgent


class ValidationAgent(BaseAgent):
    module = "validation"
    max_tokens = 6000  # one detailed validation block per idea
    system_prompt = (
        "You are a startup advisor. For each business idea provided, score it "
        "across feasibility, market fit, effort, and ROI, and produce a "
        "validation summary. Return ONLY valid JSON:\n"
        "{\n"
        '  "validations": [\n'
        "    {\n"
        '      "idea_title": "...",\n'
        '      "feasibility_score": 1,\n'
        '      "market_fit_score": 1,\n'
        '      "effort_score": 1,\n'
        '      "roi_score": 1,\n'
        '      "market_size": "...",\n'
        '      "competition_level": "low|medium|high|saturated",\n'
        '      "monetization_model": "...",\n'
        '      "revenue_potential": "...",\n'
        '      "go_to_market": "...",\n'
        '      "key_risks": ["..."],\n'
        '      "validation_summary": "...",\n'
        '      "verdict": "strong_yes|yes|maybe|no"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "All scores are integers 1–10 (effort: higher = more effort)."
    )

    def build_user_prompt(self) -> str:
        ideas = list(self.session.ideas.all())
        idea_payload = [
            {"title": i.title, "description": i.description, "category": i.category}
            for i in ideas
        ]
        return (
            f"{self._business_context()}\n\n"
            f"Score and validate each of these ideas:\n"
            f"{json.dumps(idea_payload, indent=2)}\n\n"
            "Return one validation per idea, matching the idea_title exactly."
        )

    def parse_and_save(self, payload: dict) -> None:
        validations = payload.get("validations", [])
        # Index ideas by title for easy lookup. If multiple ideas share a
        # title (unlikely but possible), the first match wins.
        ideas_by_title = {i.title: i for i in self.session.ideas.all()}

        for v in validations:
            title = v.get("idea_title", "")
            idea = ideas_by_title.get(title)
            if not idea:
                continue

            feasibility = _score(v.get("feasibility_score"))
            market_fit = _score(v.get("market_fit_score"))
            effort = _score(v.get("effort_score"))
            roi = _score(v.get("roi_score"))

            idea.feasibility_score = feasibility
            idea.market_fit_score = market_fit
            idea.effort_score = effort
            idea.roi_score = roi
            idea.overall_score = _overall(feasibility, market_fit, effort, roi)
            idea.save(
                update_fields=[
                    "feasibility_score",
                    "market_fit_score",
                    "effort_score",
                    "roi_score",
                    "overall_score",
                    "updated_at",
                ]
            )

            IdeaValidation.objects.update_or_create(
                idea=idea,
                defaults={
                    "session": self.session,
                    "market_size": str(v.get("market_size", ""))[:100],
                    "target_customer": v.get("target_customer", "") or "",
                    "problem_severity": _score(v.get("problem_severity")),
                    "solution_uniqueness": _score(v.get("solution_uniqueness")),
                    "competition_level": v.get("competition_level", "") or "",
                    "monetization_model": str(v.get("monetization_model", ""))[:100],
                    "revenue_potential": str(v.get("revenue_potential", ""))[:100],
                    "go_to_market": v.get("go_to_market", "") or "",
                    "key_risks": v.get("key_risks") or [],
                    "validation_summary": v.get("validation_summary", "") or "",
                    "verdict": v.get("verdict", "") or "",
                },
            )


def _score(value) -> int | None:
    """Coerce to a 1–10 integer or return None."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return max(1, min(10, n))


def _overall(feasibility, market_fit, effort, roi) -> Decimal | None:
    """Weighted average. Effort is inverted (lower effort scores higher)."""
    if None in (feasibility, market_fit, effort, roi):
        return None
    weighted = (
        feasibility * 0.25
        + market_fit * 0.30
        + (11 - effort) * 0.15
        + roi * 0.30
    )
    return Decimal(f"{weighted:.2f}")
