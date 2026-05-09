"""Idea generation agent. Uses competitor + trend context if available."""
from __future__ import annotations

from apps.ideas.models import Idea

from services.modules.base import BaseAgent


class IdeationAgent(BaseAgent):
    module = "ideation"
    max_tokens = 6000  # 10 ideas × ~500 tokens of structured detail
    system_prompt = (
        "You are a business strategist. Generate 10 actionable business ideas "
        "based on the business context, competitor gaps, and customer insights "
        "provided. Return ONLY valid JSON:\n"
        "{\n"
        '  "ideas": [\n'
        "    {\n"
        '      "title": "...",\n'
        '      "description": "...",\n'
        '      "category": "product|service|marketing|operations|partnership|revenue_stream",\n'
        '      "source": "competitor_gap|feedback_derived|trend_based|ai_generated",\n'
        '      "time_to_implement": "...",\n'
        '      "required_resources": ["..."],\n'
        '      "risks": ["..."],\n'
        '      "next_steps": ["Step 1...", "Step 2..."]\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    def build_user_prompt(self) -> str:
        sections = [self._business_context()]

        competitors = list(self.session.competitors.all()[:5])
        if competitors:
            sections.append("\nKnown competitors:")
            for c in competitors:
                gap = f" — Gap: {c.opportunity_gap}" if c.opportunity_gap else ""
                sections.append(f"- {c.name}: {c.description[:120]}{gap}")

        trends = list(self.session.trends.all()[:5])
        if trends:
            sections.append("\nIndustry trends:")
            for t in trends:
                sections.append(f"- {t.title} ({t.momentum}): {t.opportunity}")

        # Pull insights from any feedback submissions in this session.
        insights = []
        for sub in self.session.feedback_submissions.all():
            insights.extend(list(sub.insights.all()[:5]))
        if insights:
            sections.append("\nCustomer feedback insights:")
            for ins in insights[:10]:
                sections.append(f"- [{ins.insight_type}] {ins.title}")

        sections.append(
            "\nGenerate 10 actionable ideas. Include a mix of product, "
            "marketing, partnership, and revenue ideas."
        )
        return "\n".join(sections)

    def parse_and_save(self, payload: dict) -> None:
        for item in payload.get("ideas", []):
            Idea.objects.create(
                session=self.session,
                business=self.business,
                title=str(item.get("title", "Untitled idea"))[:255],
                description=item.get("description", "") or "",
                category=item.get("category", "") or "",
                source=item.get("source", "ai_generated") or "ai_generated",
                time_to_implement=str(item.get("time_to_implement", ""))[:50],
                required_resources=item.get("required_resources") or [],
                risks=item.get("risks") or [],
                next_steps=item.get("next_steps") or [],
            )
