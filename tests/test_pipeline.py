"""End-to-end pipeline + API tests."""
import json

import pytest
from rest_framework.test import APIClient

from apps.analysis.models import AnalysisSession
from apps.analysis.tasks import run_analysis_session
from apps.competitors.models import Competitor
from apps.ideas.models import Idea
from apps.reports.models import Report
from apps.trends.models import Trend

pytestmark = pytest.mark.django_db


def test_run_analysis_session_completes_full_pipeline(business, user):
    session = AnalysisSession.objects.create(
        business=business, user=user, llm_provider="mock"
    )
    results = run_analysis_session(str(session.id))

    session.refresh_from_db()
    assert session.status == "completed"
    assert all(v == "completed" for v in results.values())
    assert Competitor.objects.filter(session=session).exists()
    assert Trend.objects.filter(session=session).exists()
    assert Idea.objects.filter(session=session).exists()
    assert Report.objects.filter(session=session).exists()


def test_start_endpoint_runs_pipeline_synchronously(business, user, settings):
    settings.LLM_PROVIDER = "mock"
    settings.USE_DJANGO_Q = False

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post(
        "/api/analysis/start/",
        data={"business_id": str(business.id), "llm_provider": "mock"},
        format="json",
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["module_status"]["report"] == "completed"


def test_idea_patch_only_allows_user_fields(business, user):
    session = AnalysisSession.objects.create(
        business=business, user=user, llm_provider="mock"
    )
    run_analysis_session(str(session.id))

    idea = Idea.objects.filter(session=session).first()
    assert idea is not None
    original_title = idea.title

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.patch(
        f"/api/ideas/{idea.id}/",
        data={
            "is_saved": True,
            "user_rating": 4,
            "user_notes": "interesting",
            # These should be ignored by the serializer:
            "title": "HACKED",
            "overall_score": "99.99",
        },
        format="json",
    )
    assert response.status_code == 200, response.content
    body = response.json()
    assert body["is_saved"] is True
    assert body["user_rating"] == 4
    assert body["user_notes"] == "interesting"

    idea.refresh_from_db()
    assert idea.title == original_title  # writes were rejected


def test_report_export_returns_pdf(business, user):
    session = AnalysisSession.objects.create(
        business=business, user=user, llm_provider="mock"
    )
    run_analysis_session(str(session.id))

    client = APIClient()
    client.force_authenticate(user=user)
    response = client.post(f"/api/analysis/{session.id}/report/export/")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"
    assert int(response["Content-Length"]) > 1000
