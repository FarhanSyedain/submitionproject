"""Agent unit tests using the mock LLM client."""
import pytest

from apps.analysis.models import AnalysisSession, LlmLog
from apps.competitors.models import Competitor
from apps.feedback.models import FeedbackSubmission
from apps.ideas.models import Idea, IdeaValidation
from apps.reports.models import Report
from apps.trends.models import Trend
from services.modules import (
    CompetitorAgent,
    FeedbackAgent,
    IdeationAgent,
    ReportAgent,
    TrendAgent,
    ValidationAgent,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def session(business, user):
    return AnalysisSession.objects.create(
        business=business,
        user=user,
        llm_provider="mock",
        llm_model="mock-v1",
    )


def test_competitor_agent_creates_rows(session, mock_client):
    CompetitorAgent(session, mock_client).run()

    competitors = Competitor.objects.filter(session=session)
    assert competitors.count() >= 1
    first = competitors.first()
    assert first.name
    assert isinstance(first.strengths, list)

    session.refresh_from_db()
    assert session.module_status["competitor"] == "completed"
    assert session.total_tokens > 0
    assert LlmLog.objects.filter(session=session, module="competitor", success=True).exists()


def test_trend_agent_creates_rows(session, mock_client):
    TrendAgent(session, mock_client).run()
    assert Trend.objects.filter(session=session).count() >= 1


def test_ideation_then_validation_scores_ideas(session, mock_client):
    IdeationAgent(session, mock_client).run()
    assert Idea.objects.filter(session=session).count() >= 1

    ValidationAgent(session, mock_client).run()
    # Every validated idea should now have an overall_score and a Validation row.
    ideas = Idea.objects.filter(session=session)
    scored = [i for i in ideas if i.overall_score is not None]
    assert scored, "expected at least one idea to be scored"
    for idea in scored:
        assert 1 <= idea.feasibility_score <= 10
        assert idea.overall_score is not None
    assert IdeaValidation.objects.filter(session=session).count() >= 1


def test_report_agent_writes_report(session, mock_client):
    IdeationAgent(session, mock_client).run()
    ValidationAgent(session, mock_client).run()
    ReportAgent(session, mock_client).run()

    report = Report.objects.get(session=session)
    assert report.executive_summary
    assert report.recommended_actions
    assert report.business == session.business


def test_feedback_agent_extracts_insights(session, mock_client):
    submission = FeedbackSubmission.objects.create(
        session=session,
        business=session.business,
        raw_text="Onboarding is confusing. Love the AI ideas.",
    )
    FeedbackAgent(submission, mock_client).run()
    assert submission.insights.count() >= 1


def test_failure_marks_module_failed(session, mock_client, monkeypatch):
    """A parse error in an agent should mark the module failed but not raise from run()."""

    def boom(*_args, **_kwargs):
        raise RuntimeError("kaboom")

    agent = CompetitorAgent(session, mock_client)
    monkeypatch.setattr(agent, "parse_and_save", boom)
    with pytest.raises(RuntimeError):
        agent.run()

    session.refresh_from_db()
    assert session.module_status["competitor"] == "failed"
    assert LlmLog.objects.filter(session=session, success=False).exists()
