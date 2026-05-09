"""Report compilation agent. Reads everything else and writes a Report row."""
from __future__ import annotations

import json

from apps.reports.models import Report

from services.modules.base import BaseAgent


class ReportAgent(BaseAgent):
    module = "report"
    max_tokens = 3000  # exec summary + insights + actions
    system_prompt = (
        "You are a business consultant. Write a concise executive summary, "
        "a list of key insights, and a list of recommended actions based on "
        "all analysis modules provided. Return ONLY valid JSON:\n"
        "{\n"
        '  "executive_summary": "...",\n'
        '  "key_insights": ["...", "..."],\n'
        '  "recommended_actions": [\n'
        '    {"action": "...", "priority": "high|medium|low", "timeline": "..."}\n'
        "  ]\n"
        "}"
    )

    def build_user_prompt(self) -> str:
        sections = [self._business_context()]

        competitors = list(self.session.competitors.all()[:5])
        if competitors:
            sections.append("\nCompetitors:")
            for c in competitors:
                sections.append(f"- {c.name}: gap={c.opportunity_gap[:120]}")

        trends = list(self.session.trends.all()[:5])
        if trends:
            sections.append("\nTrends:")
            for t in trends:
                sections.append(f"- {t.title} ({t.momentum}): {t.opportunity[:120]}")

        # Pull top-scoring ideas to feature in the summary.
        top_ideas = list(
            self.session.ideas.exclude(overall_score=None).order_by("-overall_score")[:5]
        )
        if top_ideas:
            sections.append("\nTop ideas:")
            for i in top_ideas:
                verdict = ""
                try:
                    verdict = f" [{i.validation.verdict}]"
                except Exception:
                    pass
                sections.append(f"- {i.title} ({i.overall_score}){verdict}")

        sections.append(
            "\nWrite a concise executive summary (3–5 sentences), 3–5 key "
            "insights, and 3–5 prioritised recommended actions."
        )
        return "\n".join(sections)

    def parse_and_save(self, payload: dict) -> None:
        top_idea_ids = list(
            self.session.ideas.exclude(overall_score=None)
            .order_by("-overall_score")
            .values_list("id", flat=True)[:3]
        )

        Report.objects.update_or_create(
            session=self.session,
            defaults={
                "business": self.business,
                "user": self.session.user,
                "title": f"Analysis report — {self.business.name}",
                "executive_summary": payload.get("executive_summary", "") or "",
                "top_ideas": [str(i) for i in top_idea_ids],
                "key_insights": payload.get("key_insights") or [],
                "recommended_actions": payload.get("recommended_actions") or [],
            },
        )
