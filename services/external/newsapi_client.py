"""Tiny NewsAPI client (https://newsapi.org).

Free tier is 100 requests/day. We use this to ground the TrendAgent in
real, recent headlines rather than relying on the LLM's training-data
recall.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import requests


class NewsAPIClient:
    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: str, timeout: int = 10) -> None:
        if not api_key:
            raise ValueError("NEWS_API_KEY is required for NewsAPIClient")
        self.api_key = api_key
        self.timeout = timeout

    def search(
        self,
        query: str,
        *,
        days: int = 14,
        page_size: int = 10,
        language: str = "en",
        sort_by: str = "publishedAt",
    ) -> list[dict]:
        """Return up to `page_size` recent articles matching `query`.

        Each item has at minimum: title, description, url, source.name,
        publishedAt. See https://newsapi.org/docs/endpoints/everything.
        """
        if not query.strip():
            return []

        from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
        params = {
            "q": query,
            "from": from_date,
            "language": language,
            "sortBy": sort_by,
            "pageSize": min(max(page_size, 1), 100),
            "apiKey": self.api_key,
        }
        response = requests.get(
            f"{self.BASE_URL}/everything", params=params, timeout=self.timeout
        )
        response.raise_for_status()
        data = response.json()
        if data.get("status") != "ok":
            raise RuntimeError(
                f"NewsAPI error: {data.get('message', 'unknown')}"
            )
        return data.get("articles", []) or []

    def headlines(self, query: str = "", category: str = "", *, page_size: int = 10) -> list[dict]:
        params = {
            "language": "en",
            "pageSize": min(max(page_size, 1), 100),
            "apiKey": self.api_key,
        }
        if query:
            params["q"] = query
        if category:
            params["category"] = category
        response = requests.get(
            f"{self.BASE_URL}/top-headlines", params=params, timeout=self.timeout
        )
        response.raise_for_status()
        return response.json().get("articles", []) or []
