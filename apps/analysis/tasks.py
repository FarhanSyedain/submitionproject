"""Async (or sync) analysis pipeline.

`run_analysis_session` is the entry point. It runs the agent chain in order:
competitor → trends → ideation → validation → report. If one agent fails,
its module is marked failed and the rest still run.

In dev (USE_DJANGO_Q=False) this runs synchronously inside the request.
In prod (USE_DJANGO_Q=True) the API enqueues it and a worker process picks
it up.
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.utils import timezone

from services.llm import get_llm_client
from services.modules import (
    CompetitorAgent,
    IdeationAgent,
    ReportAgent,
    TrendAgent,
    ValidationAgent,
)

logger = logging.getLogger(__name__)

PIPELINE = [
    ("competitor", CompetitorAgent),
    ("trends", TrendAgent),
    ("ideation", IdeationAgent),
    ("validation", ValidationAgent),
    ("report", ReportAgent),
]


def run_analysis_session(session_id: str) -> dict:
    """Run the full agent chain on a session. Returns a per-module status dict."""
    from apps.analysis.models import AnalysisSession
    from services.memory import unload_translator

    # Free memory the HF translator may be holding before we load the LLM.
    unload_translator()

    session = AnalysisSession.objects.get(pk=session_id)

    # Initialise per-module status so the UI can render a progress list
    # before the first agent finishes.
    session.status = "running"
    session.module_status = {name: "pending" for name, _ in PIPELINE}
    session.error_message = ""
    session.save(update_fields=["status", "module_status", "error_message"])

    client = get_llm_client(session.llm_provider)
    session.llm_provider = client.provider
    session.llm_model = client.model
    session.save(update_fields=["llm_provider", "llm_model"])

    results: dict[str, str] = {}
    for module_name, agent_cls in PIPELINE:
        try:
            agent = agent_cls(session, client)
            agent.run()
            results[module_name] = "completed"
        except Exception as exc:
            logger.exception("Agent %s failed on session %s", module_name, session.pk)
            results[module_name] = "failed"
            # Per agent, _update_status('failed') already ran in BaseAgent;
            # we keep going so other modules still produce output.

    session.refresh_from_db()
    any_completed = any(v == "completed" for v in results.values())
    session.status = "completed" if any_completed else "failed"
    session.completed_at = timezone.now()
    if not any_completed:
        session.error_message = "All agents failed; see llm_logs for details."
    session.save(update_fields=["status", "completed_at", "error_message"])

    # Background-style Kashmiri localisation:
    # We flip the session to "completed" *before* this so the UI surfaces the
    # English report immediately. The localiser then translates + synthesises
    # narration and stamps the result onto the Report row. Reopening this
    # session in the future will hit the cache and skip both steps.
    if results.get("report") == "completed":
        try:
            from apps.reports.localization import generate_localization
            from apps.reports.models import Report

            report = Report.objects.filter(session=session).first()
            if report is not None:
                generate_localization(report)
        except Exception:
            logger.exception(
                "Localization step crashed for session %s", session.pk
            )

    return results


def enqueue_analysis_session(session_id: str) -> None:
    """Run the analysis inline or push it onto the Django Q queue."""
    if not settings.USE_DJANGO_Q:
        run_analysis_session(str(session_id))
        return

    from django_q.tasks import async_task

    async_task("apps.analysis.tasks.run_analysis_session", str(session_id))
