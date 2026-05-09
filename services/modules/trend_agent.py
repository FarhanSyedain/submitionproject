"""Industry trend mapping agent.

When NEWS_API_KEY is set, the agent fetches recent headlines for the
business's industry and feeds them into the prompt so the LLM is grounded
in real news rather than relying on training-data recall.
"""
from __future__ import annotations

import logging

from django.conf import settings

from apps.trends.models import Trend

from services.modules.base import BaseAgent

logger = logging.getLogger(__name__)


class TrendAgent(BaseAgent):
    module = "trends"
    max_tokens = 3500  # 5 trends × description × source URL list
    system_prompt = (
        "You are a market trends analyst. Identify 5 key industry trends "
        "relevant to this business and map each to an opportunity and a "
        "threat. Return ONLY valid JSON:\n"
        "{\n"
        '  "trends": [\n'
        "    {\n"
        '      "title": "...",\n'
        '      "description": "...",\n'
        '      "trend_type": "technology|consumer_behavior|regulation|market|social",\n'
        '      "momentum": "emerging|rising|peaking|declining",\n'
        '      "relevance_score": 1,\n'
        '      "opportunity": "...",\n'
        '      "threat": "...",\n'
        '      "source_urls": ["..."]\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "relevance_score is an integer 1–10. If recent news headlines are "
        "provided, cite the URLs of relevant articles in source_urls."
    )

    def build_user_prompt(self) -> str:
        sections = [self._business_context()]

        articles = self._fetch_news()
        if articles:
            sections.append(
                f"\nRecent news headlines (last 14 days, {len(articles)} items):"
            )
            for a in articles:
                title = (a.get("title") or "").strip()
                source = (a.get("source") or {}).get("name") or "?"
                url = a.get("url") or ""
                published = (a.get("publishedAt") or "")[:10]
                sections.append(f"- {title}  ({source}, {published})  {url}")

        sections.append(
            "\nIdentify the top 5 industry trends relevant to this business "
            "and return them as JSON. If you used the headlines above, cite "
            "their URLs in source_urls."
        )
        return "\n".join(sections)

    def _fetch_news(self) -> list[dict]:
        api_key = getattr(settings, "NEWS_API_KEY", "")
        if not api_key:
            return []

        # Build a query from the most specific signal we have.
        query = (
            self.business.industry
            or self.business.target_market
            or self.business.name
        )
        if not query:
            return []

        try:
            from services.external.newsapi_client import NewsAPIClient

            client = NewsAPIClient(api_key)
            return client.search(query, days=14, page_size=10)
        except Exception as exc:  # noqa: BLE001
            logger.warning("NewsAPI fetch failed (%s); proceeding without news", exc)
            return []

    def parse_and_save(self, payload: dict) -> None:
        for item in payload.get("trends", []):
            Trend.objects.create(
                session=self.session,
                business=self.business,
                title=str(item.get("title", "Untitled trend"))[:255],
                description=item.get("description", "") or "",
                trend_type=item.get("trend_type", "") or "",
                momentum=item.get("momentum", "rising") or "rising",
                relevance_score=_safe_int(item.get("relevance_score")),
                opportunity=item.get("opportunity", "") or "",
                threat=item.get("threat", "") or "",
                source_urls=item.get("source_urls") or [],
            )


def _safe_int(value, default: int | None = None) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
