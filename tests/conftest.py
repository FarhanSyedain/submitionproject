"""Shared pytest fixtures."""
import os

os.environ.setdefault("LLM_PROVIDER", "mock")

import pytest
from django.contrib.auth import get_user_model

from apps.business.models import BusinessProfile

User = get_user_model()


@pytest.fixture(autouse=True)
def _no_external_apis(settings):
    """Don't burn live API quota during tests."""
    settings.NEWS_API_KEY = ""
    settings.SERPAPI_KEY = ""


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="alice",
        email="alice@zeaniv.local",
        password="testpass123",
        full_name="Alice Tester",
    )


@pytest.fixture
def business(db, user):
    return BusinessProfile.objects.create(
        user=user,
        name="Test Co",
        description="A test business that sells widgets to small businesses.",
        industry="SaaS",
        target_market="SMB",
        stage="startup",
    )


@pytest.fixture
def mock_client():
    from services.llm.mock_client import MockClient

    return MockClient()
