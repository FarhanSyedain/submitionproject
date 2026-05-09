"""Tiny SerpAPI client (https://serpapi.com).

Free tier is 100 searches/month. We use it to ground the CompetitorAgent
in real Google search results so the LLM extracts existing products
rather than hallucinating plausible-sounding brand names.
"""
from __future__ import annotations

import requests


class SerpAPIClient:
    BASE_URL = "https://serpapi.com/search"

    def __init__(self, api_key: str, timeout: int = 15) -> None:
        if not api_key:
            raise ValueError("SERPAPI_KEY is required for SerpAPIClient")
        self.api_key = api_key
        self.timeout = timeout

    def search(
        self,
        query: str,
        *,
        num: int = 10,
        engine: str = "google",
        hl: str = "en",
        gl: str = "us",
    ) -> dict:
        """Run a Google search and return the raw SerpAPI payload.

        Use `organic_results` (a list of dicts) for the bulk of the data —
        each item has at least `title`, `link`, and `snippet`.
        """
        params = {
            "q": query,
            "engine": engine,
            "num": num,
            "hl": hl,
            "gl": gl,
            "api_key": self.api_key,
        }
        response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def organic(self, query: str, *, num: int = 10) -> list[dict]:
        """Convenience: just the organic results list."""
        data = self.search(query, num=num)
        return data.get("organic_results", []) or []
