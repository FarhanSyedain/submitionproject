"""Hardcoded JSON responses for offline / no-cost development.

Each agent passes its `module` name; the mock returns canned data for that
module. Anything unrecognised falls back to an empty `{}` so callers still
get a valid JSON object to iterate over.
"""
from __future__ import annotations

import json
import time

from services.llm.base import BaseLLMClient, CompletionResult

MOCK_RESPONSES: dict[str, dict] = {
    "competitor": {
        "competitors": [
            {
                "name": "Acme Analytics",
                "website": "https://acme-analytics.example",
                "description": "Established BI platform aimed at mid-market.",
                "strengths": ["strong brand", "deep integrations"],
                "weaknesses": ["expensive", "slow onboarding"],
                "market_position": "leader",
                "estimated_size": "enterprise",
                "threat_level": 4,
                "opportunity_gap": "Underserves solo founders and pre-seed startups.",
            },
            {
                "name": "Insightly Lite",
                "website": "https://insightly-lite.example",
                "description": "Freemium BI tool with limited features.",
                "strengths": ["free tier", "easy signup"],
                "weaknesses": ["shallow analysis", "no AI"],
                "market_position": "challenger",
                "estimated_size": "smb",
                "threat_level": 2,
                "opportunity_gap": "No AI-driven idea generation.",
            },
            {
                "name": "MarketMind",
                "website": "https://marketmind.example",
                "description": "Niche competitive-intelligence consultancy.",
                "strengths": ["expert analysts", "white-glove service"],
                "weaknesses": ["non-self-serve", "high price"],
                "market_position": "niche",
                "estimated_size": "smb",
                "threat_level": 3,
                "opportunity_gap": "Slow turnaround, no real-time insights.",
            },
        ]
    },
    "feedback": {
        "insights": [
            {
                "insight_type": "pain_point",
                "title": "Onboarding is confusing",
                "description": "New users struggle to find the analysis dashboard.",
                "frequency_score": 8,
                "sentiment": "negative",
                "priority": "high",
                "example_quotes": [
                    "I had no idea where to start after signing up.",
                    "Took me 20 minutes to find the report button.",
                ],
            },
            {
                "insight_type": "feature_request",
                "title": "Export to PowerPoint",
                "description": "Multiple users want PPT export in addition to PDF.",
                "frequency_score": 6,
                "sentiment": "neutral",
                "priority": "medium",
                "example_quotes": ["A PPT version would be amazing for board meetings."],
            },
            {
                "insight_type": "compliment",
                "title": "AI ideas are surprisingly good",
                "description": "Users are impressed with the quality of generated ideas.",
                "frequency_score": 5,
                "sentiment": "positive",
                "priority": "low",
                "example_quotes": ["Half of these ideas I would actually try."],
            },
        ]
    },
    "trends": {
        "trends": [
            {
                "title": "AI-native BI tools",
                "description": "Customers increasingly expect chat-style analysis built in.",
                "trend_type": "technology",
                "momentum": "rising",
                "relevance_score": 9,
                "opportunity": "Position Zeaniv as AI-first from day one.",
                "threat": "Larger BI vendors are bolting on LLM features fast.",
            },
            {
                "title": "Indie founder boom",
                "description": "More solo founders launching micro-SaaS businesses.",
                "trend_type": "market",
                "momentum": "rising",
                "relevance_score": 8,
                "opportunity": "Target solo founders with a free / low-cost tier.",
                "threat": "Crowded market, low willingness to pay.",
            },
            {
                "title": "Privacy-first analytics",
                "description": "GDPR and similar regs push tools to keep data local.",
                "trend_type": "regulation",
                "momentum": "peaking",
                "relevance_score": 6,
                "opportunity": "Offer local-LLM (Ollama) deployment as a differentiator.",
                "threat": "Compliance work adds engineering cost.",
            },
        ]
    },
    "ideation": {
        "ideas": [
            {
                "title": "Guided onboarding tour",
                "description": "Interactive walkthrough that runs the first analysis for the user.",
                "category": "product",
                "source": "feedback_derived",
                "time_to_implement": "1-3 weeks",
                "required_resources": ["frontend dev", "designer"],
                "risks": ["users skip the tour"],
                "next_steps": ["Define tour script", "Build overlay component", "A/B test"],
            },
            {
                "title": "Ollama local-deploy edition",
                "description": "Self-hosted version that runs entirely on a user's machine.",
                "category": "product",
                "source": "trend_based",
                "time_to_implement": "1-3 months",
                "required_resources": ["backend dev", "devops"],
                "risks": ["support burden", "model quality varies"],
                "next_steps": ["Spec local mode", "Package as Docker", "Write docs"],
            },
            {
                "title": "PowerPoint export",
                "description": "One-click export of the report to .pptx.",
                "category": "product",
                "source": "feedback_derived",
                "time_to_implement": "1-2 weeks",
                "required_resources": ["backend dev"],
                "risks": ["template maintenance"],
                "next_steps": ["Pick template lib", "Map report sections to slides"],
            },
            {
                "title": "Indie-founder tier",
                "description": "$9/mo plan with limited monthly analyses, aimed at solo founders.",
                "category": "revenue_stream",
                "source": "trend_based",
                "time_to_implement": "1-3 weeks",
                "required_resources": ["product manager", "billing integration"],
                "risks": ["cannibalises higher tiers"],
                "next_steps": ["Validate price point", "Wire Stripe", "Launch beta"],
            },
            {
                "title": "Competitor watchlist",
                "description": "Save competitors and get a weekly diff email.",
                "category": "product",
                "source": "competitor_gap",
                "time_to_implement": "1-2 months",
                "required_resources": ["backend dev", "scraper / serpapi"],
                "risks": ["scraping breaks"],
                "next_steps": ["Design watchlist UI", "Build diff engine", "Wire email"],
            },
        ]
    },
    "validation": {
        "validations": [
            {
                "idea_title": "Guided onboarding tour",
                "feasibility_score": 9,
                "market_fit_score": 8,
                "effort_score": 3,
                "roi_score": 8,
                "market_size": "Internal — improves conversion",
                "competition_level": "low",
                "monetization_model": "indirect (activation)",
                "revenue_potential": "+15% activation rate",
                "go_to_market": "Ship to all new signups, A/B test.",
                "key_risks": ["users dismiss tour"],
                "validation_summary": "Cheap, high-impact UX win — do it first.",
                "verdict": "strong_yes",
            },
            {
                "idea_title": "Ollama local-deploy edition",
                "feasibility_score": 6,
                "market_fit_score": 7,
                "effort_score": 8,
                "roi_score": 6,
                "market_size": "~$500M privacy-conscious BI segment",
                "competition_level": "low",
                "monetization_model": "one-time license + support",
                "revenue_potential": "$50k-200k/yr at scale",
                "go_to_market": "Launch on HackerNews + privacy subreddits.",
                "key_risks": ["support burden", "Ollama model quality"],
                "validation_summary": "Differentiated but heavy lift; defer to v2.",
                "verdict": "maybe",
            },
            {
                "idea_title": "PowerPoint export",
                "feasibility_score": 9,
                "market_fit_score": 6,
                "effort_score": 2,
                "roi_score": 5,
                "market_size": "All paid users",
                "competition_level": "medium",
                "monetization_model": "feature in paid tier",
                "revenue_potential": "Reduces churn ~5%",
                "go_to_market": "Bundle into Pro tier, announce in changelog.",
                "key_risks": ["template upkeep"],
                "validation_summary": "Easy lift, modest impact — quick win.",
                "verdict": "yes",
            },
            {
                "idea_title": "Indie-founder tier",
                "feasibility_score": 8,
                "market_fit_score": 9,
                "effort_score": 4,
                "roi_score": 7,
                "market_size": "~$2B indie SaaS market",
                "competition_level": "high",
                "monetization_model": "SaaS (low-tier subscription)",
                "revenue_potential": "$10k-50k MRR within 6 months",
                "go_to_market": "Launch on Indie Hackers + Twitter.",
                "key_risks": ["cannibalisation", "support volume"],
                "validation_summary": "Strong fit with rising indie segment.",
                "verdict": "yes",
            },
            {
                "idea_title": "Competitor watchlist",
                "feasibility_score": 7,
                "market_fit_score": 8,
                "effort_score": 6,
                "roi_score": 7,
                "market_size": "Mid-market BI buyers",
                "competition_level": "medium",
                "monetization_model": "premium add-on",
                "revenue_potential": "$20-50k MRR",
                "go_to_market": "Sell as upsell to existing accounts.",
                "key_risks": ["scraper reliability", "false-positive diffs"],
                "validation_summary": "Good upsell once core is solid.",
                "verdict": "yes",
            },
        ]
    },
    "report": {
        "executive_summary": (
            "Zeaniv AI is well-positioned to capture the rising indie-founder "
            "segment by leaning into AI-native analysis and self-serve onboarding. "
            "Focus the next quarter on activation (guided tour) and a low-cost tier; "
            "defer heavier infrastructure plays like local-deploy until v2."
        ),
        "key_insights": [
            "Onboarding friction is the #1 customer complaint — fixing it unlocks the rest.",
            "AI-native BI is the dominant trend; competitors are racing to bolt it on.",
            "Indie founders are an underserved, fast-growing segment that fits Zeaniv's price point.",
        ],
        "recommended_actions": [
            {
                "action": "Ship guided onboarding tour",
                "priority": "high",
                "timeline": "next 2 weeks",
            },
            {
                "action": "Launch indie-founder pricing tier",
                "priority": "high",
                "timeline": "next 4 weeks",
            },
            {
                "action": "Add PowerPoint export",
                "priority": "medium",
                "timeline": "next 2 weeks",
            },
            {
                "action": "Prototype Ollama local-deploy edition",
                "priority": "low",
                "timeline": "Q3",
            },
        ],
    },
}


class MockClient(BaseLLMClient):
    provider = "mock"
    model = "mock-v1"

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = 2000,
        module: str = "",
    ) -> CompletionResult:
        start = time.perf_counter()
        payload = MOCK_RESPONSES.get(module, {})
        text = json.dumps(payload)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        # Fake but plausible token counts so dashboards aren't all zeros.
        return CompletionResult(
            text=text,
            prompt_tokens=len(system + user) // 4,
            completion_tokens=len(text) // 4,
            latency_ms=elapsed_ms,
        )
