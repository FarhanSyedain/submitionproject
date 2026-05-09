"""Competitor intelligence agent.

When SERPAPI_KEY is set, the agent runs a Google search for "<industry>
competitors / alternatives" first and feeds the top organic results into
the prompt so the LLM extracts real products instead of hallucinating
plausible-sounding brand names.
"""
from __future__ import annotations

import logging

from django.conf import settings

from apps.competitors.models import Competitor

from services.modules.base import BaseAgent

logger = logging.getLogger(__name__)


class CompetitorAgent(BaseAgent):
    module = "competitor"
    max_tokens = 3500  # 5 competitors × strengths/weaknesses arrays
    system_prompt = (
        "You are a business intelligence analyst. Given a business description "
        "(and optionally a list of search results suggesting competitors), "
        "identify 5 real competitors. Prefer real products mentioned in the "
        "search results over inventing names. Return ONLY valid JSON matching "
        "this schema:\n"
        "{\n"
        '  "competitors": [\n'
        "    {\n"
        '      "name": "...",\n'
        '      "website": "...",\n'
        '      "description": "...",\n'
        '      "strengths": ["...", "..."],\n'
        '      "weaknesses": ["...", "..."],\n'
        '      "market_position": "leader|challenger|niche|new",\n'
        '      "estimated_size": "startup|smb|enterprise",\n'
        '      "threat_level": 1,\n'
        '      "opportunity_gap": "...",\n'
        '      "source_url": "..."\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "threat_level is an integer 1–5. If you used a search result, set "
        "source_url to the URL it came from."
    )

    def build_user_prompt(self) -> str:
        sections = [self._business_context()]

        results = self._fetch_search_results()
        if results:
            sections.append(
                f"\nGoogle search results suggesting competitors ({len(results)} hits):"
            )
            for r in results:
                title = (r.get("title") or "").strip()
                link = r.get("link") or ""
                snippet = (r.get("snippet") or "").strip()
                sections.append(f"- {title}  ({link})\n  {snippet}")

        sections.append(
            "\nIdentify 5 real competitors and return them as JSON. "
            "Prefer products from the search results above when relevant."
        )
        return "\n".join(sections)

    def _fetch_search_results(self) -> list[dict]:
        api_key = getattr(settings, "SERPAPI_KEY", "")
        if not api_key:
            return []

        # Build the most useful query from what we know.
        seed = self.business.industry or self.business.target_market
        if seed and self.business.name:
            query = f"best {seed} tools competitors alternatives"
        elif self.business.description:
            # Fallback: use the first ~80 chars of the description.
            short = self.business.description[:80].strip()
            query = f"{short} competitors alternatives"
        else:
            return []

        try:
            from services.external.serpapi_client import SerpAPIClient

            return SerpAPIClient(api_key).organic(query, num=10)
        except Exception as exc:  # noqa: BLE001
            logger.warning("SerpAPI fetch failed (%s); proceeding without it", exc)
            return []

    def parse_and_save(self, payload: dict) -> None:
        for item in payload.get("competitors", []):
            Competitor.objects.create(
                session=self.session,
                business=self.business,
                name=str(item.get("name", "Unknown"))[:255],
                website=str(item.get("website", ""))[:500],
                description=item.get("description", "") or "",
                strengths=item.get("strengths") or [],
                weaknesses=item.get("weaknesses") or [],
                market_position=item.get("market_position", "") or "",
                estimated_size=item.get("estimated_size", "") or "",
                threat_level=int(item.get("threat_level", 3) or 3),
                opportunity_gap=item.get("opportunity_gap", "") or "",
                source_url=item.get("source_url", "") or "",
            )
