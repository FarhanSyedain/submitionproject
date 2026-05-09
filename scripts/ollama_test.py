"""Run a single agent against the live Ollama daemon and report what we got.

Useful as a sanity check that the local model can actually return parseable
JSON for our schemas. Defaults to the CompetitorAgent because its schema is
the simplest; pass --module {competitor,trends,ideation,validation,report}
to try others.

Run:  python scripts/ollama_test.py [--module trends] [--model llama3.2]
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402

from apps.analysis.models import AnalysisSession  # noqa: E402
from apps.business.models import BusinessProfile  # noqa: E402
from services.llm.ollama_client import OllamaClient  # noqa: E402
from services.modules import (  # noqa: E402
    CompetitorAgent,
    IdeationAgent,
    ReportAgent,
    TrendAgent,
    ValidationAgent,
)

AGENTS = {
    "competitor": CompetitorAgent,
    "trends": TrendAgent,
    "ideation": IdeationAgent,
    "validation": ValidationAgent,
    "report": ReportAgent,
}

User = get_user_model()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--module", default="competitor", choices=list(AGENTS))
    parser.add_argument("--model", default="llama3.2")
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama daemon URL",
    )
    args = parser.parse_args()

    # Setup: a stable demo user + business profile so we can re-run safely.
    user, _ = User.objects.get_or_create(
        username="ollama_test",
        defaults={"email": "ollama_test@zeaniv.local", "full_name": "Ollama Test"},
    )
    business, _ = BusinessProfile.objects.get_or_create(
        user=user,
        name="Zeaniv Demo",
        defaults={
            "description": (
                "AI-native business intelligence platform that helps solo "
                "founders generate and validate startup ideas in minutes."
            ),
            "industry": "SaaS",
            "target_market": "Solo founders & indie hackers",
            "stage": "idea",
        },
    )
    session = AnalysisSession.objects.create(
        business=business,
        user=user,
        llm_provider="ollama",
        llm_model=args.model,
    )

    client = OllamaClient(base_url=args.base_url, model=args.model)
    agent_cls = AGENTS[args.module]

    print(f"Module:   {args.module}")
    print(f"Model:    {args.model}")
    print(f"Session:  {session.id}\n")
    print("Running agent (first call cold-loads the model — can take 10–30s)…")

    # For the agents that depend on prior data, run their prerequisites first.
    if args.module in ("ideation", "validation", "report"):
        print("\n[prereq] CompetitorAgent")
        _time(CompetitorAgent(session, client).run)
        print("[prereq] TrendAgent")
        _time(TrendAgent(session, client).run)
    if args.module in ("validation", "report"):
        print("[prereq] IdeationAgent")
        _time(IdeationAgent(session, client).run)
    if args.module == "report":
        print("[prereq] ValidationAgent")
        _time(ValidationAgent(session, client).run)

    print(f"\n[target] {agent_cls.__name__}")
    elapsed = _time(agent_cls(session, client).run)

    session.refresh_from_db()
    print(f"\nStatus:  {session.module_status.get(agent_cls.module)}")
    print(f"Tokens:  {session.total_tokens}")
    print(f"Latency: {elapsed:.1f}s")

    # Summarise what we got.
    if args.module == "competitor":
        rows = list(session.competitors.all())
        print(f"\nGot {len(rows)} competitor rows:")
        for r in rows:
            print(f"  • {r.name} (threat {r.threat_level}/5)")
            if r.opportunity_gap:
                print(f"      gap: {r.opportunity_gap[:100]}")
    elif args.module == "trends":
        rows = list(session.trends.all())
        print(f"\nGot {len(rows)} trend rows:")
        for r in rows:
            print(f"  • {r.title}  [{r.momentum}, relevance {r.relevance_score}]")
    elif args.module == "ideation":
        rows = list(session.ideas.all())
        print(f"\nGot {len(rows)} idea rows:")
        for r in rows:
            print(f"  • {r.title}  [{r.category}]")
    elif args.module == "validation":
        rows = list(session.ideas.exclude(overall_score=None))
        print(f"\nScored {len(rows)} ideas:")
        for r in rows:
            verdict = ""
            try:
                verdict = f" [{r.validation.verdict}]"
            except Exception:
                pass
            print(f"  • {r.overall_score:>5}  {r.title}{verdict}")
    elif args.module == "report":
        report = session.report
        print(f"\nReport:\n  exec summary: {report.executive_summary[:160]}…")
        print(f"  insights: {len(report.key_insights)}, actions: {len(report.recommended_actions)}")


def _time(fn) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


if __name__ == "__main__":
    main()
