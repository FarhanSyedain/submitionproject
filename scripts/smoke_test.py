"""End-to-end smoke test for the Zeaniv backend.

Hits every wired-up endpoint via Django's test client (no live server needed).
Uses LLM_PROVIDER=mock so it runs offline and free.

Run:  python scripts/smoke_test.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
os.environ.setdefault("LLM_PROVIDER", "mock")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402

User = get_user_model()


def step(label: str) -> None:
    print(f"\n── {label} ──")


def show(label: str, response) -> dict | list:
    body = response.json() if response.content else {}
    summary = body
    if isinstance(body, dict) and "results" in body:
        summary = f"<paginated, {len(body['results'])} items>"
    elif isinstance(body, list):
        summary = f"<list, {len(body)} items>"
    print(f"  {label}: {response.status_code}  {summary if isinstance(summary, str) else ''}")
    return body


def assert_ok(label: str, response, *expected: int) -> None:
    if response.status_code not in expected:
        body = response.content.decode(errors="replace")
        raise SystemExit(f"FAIL {label}: got {response.status_code}, expected {expected}\n{body}")


def main() -> None:
    # Fresh demo user so the test is repeatable (delete leftover state).
    User.objects.filter(username__in=["demo", "smoketest"]).delete()
    print("Cleared previous demo / smoketest users.")

    c = Client()

    # 1) Register a real user and grab tokens
    step("POST /api/auth/register/")
    r = c.post(
        "/api/auth/register/",
        data=json.dumps(
            {
                "username": "smoketest",
                "email": "smoketest@zeaniv.local",
                "password": "smokepass123",
                "full_name": "Smoke Test",
                "company_name": "Zeaniv",
                "industry": "SaaS",
            }
        ),
        content_type="application/json",
    )
    assert_ok("register", r, 201)
    body = show("register", r)
    access = body["access"]
    auth_header = {"HTTP_AUTHORIZATION": f"Bearer {access}"}

    # 2) GET /api/auth/me/
    step("GET /api/auth/me/")
    r = c.get("/api/auth/me/", **auth_header)
    assert_ok("me", r, 200)
    show("me", r)

    # 3) Create a business
    step("POST /api/businesses/")
    r = c.post(
        "/api/businesses/",
        data=json.dumps(
            {
                "name": "Zeaniv Demo",
                "description": (
                    "AI-native business intelligence platform that helps solo "
                    "founders generate and validate startup ideas."
                ),
                "industry": "SaaS",
                "target_market": "Solo founders & indie hackers",
                "stage": "idea",
            }
        ),
        content_type="application/json",
        **auth_header,
    )
    assert_ok("create business", r, 201)
    body = show("create business", r)
    business_id = body["id"]

    # 4) List businesses
    step("GET /api/businesses/")
    r = c.get("/api/businesses/", **auth_header)
    assert_ok("list businesses", r, 200)
    show("list businesses", r)

    # 5) Start an analysis (mock provider, runs synchronously)
    step("POST /api/analysis/start/")
    r = c.post(
        "/api/analysis/start/",
        data=json.dumps({"business_id": business_id, "llm_provider": "mock"}),
        content_type="application/json",
        **auth_header,
    )
    assert_ok("start analysis", r, 201)
    body = show("start analysis", r)
    session_id = body["id"]
    print(f"  session status: {body['status']}, modules: {body['module_status']}")
    print(f"  total_tokens: {body['total_tokens']}")

    # 6) Status endpoint
    step(f"GET /api/analysis/{session_id}/status/")
    r = c.get(f"/api/analysis/{session_id}/status/", **auth_header)
    assert_ok("status", r, 200)
    show("status", r)

    # 7) Each module endpoint
    for module in ("competitors", "trends", "ideas", "validation"):
        step(f"GET /api/analysis/{session_id}/{module}/")
        r = c.get(f"/api/analysis/{session_id}/{module}/", **auth_header)
        assert_ok(module, r, 200)
        show(module, r)

    # 8) Report
    step(f"GET /api/analysis/{session_id}/report/")
    r = c.get(f"/api/analysis/{session_id}/report/", **auth_header)
    assert_ok("report", r, 200)
    body = show("report", r)
    print(f"  exec summary: {body.get('executive_summary', '')[:120]}...")

    # 9) Submit feedback
    step(f"POST /api/analysis/{session_id}/feedback/submit/")
    r = c.post(
        f"/api/analysis/{session_id}/feedback/submit/",
        data=json.dumps(
            {
                "raw_text": (
                    "I love the AI ideas, but the onboarding is confusing — "
                    "I had no idea where to find my first analysis."
                ),
                "source_type": "manual",
            }
        ),
        content_type="application/json",
        **auth_header,
    )
    assert_ok("submit feedback", r, 201)
    body = show("submit feedback", r)
    print(f"  insights extracted: {len(body.get('insights', []))}")

    # 10) Patch an idea
    step("GET ideas → PATCH first idea")
    r = c.get(f"/api/analysis/{session_id}/ideas/", **auth_header)
    ideas = r.json().get("results", r.json())
    assert ideas, "expected at least one idea after the mock run"
    first = ideas[0]
    print(f"  patching idea: {first['title']}")
    r = c.patch(
        f"/api/ideas/{first['id']}/",
        data=json.dumps(
            {"is_saved": True, "user_rating": 5, "user_notes": "love this one"}
        ),
        content_type="application/json",
        **auth_header,
    )
    assert_ok("patch idea", r, 200)
    body = show("patch idea", r)
    assert body["is_saved"] is True
    assert body["user_rating"] == 5

    # 11) Rerun the analysis (should clear prior rows and produce fresh ones)
    step(f"POST /api/analysis/{session_id}/rerun/")
    r = c.post(f"/api/analysis/{session_id}/rerun/", **auth_header)
    assert_ok("rerun", r, 200)
    body = show("rerun", r)
    print(f"  status after rerun: {body['status']}")

    # 12) Report PDF export
    step(f"POST /api/analysis/{session_id}/report/export/")
    r = c.post(f"/api/analysis/{session_id}/report/export/", **auth_header)
    assert_ok("export", r, 200)
    assert r["Content-Type"] == "application/pdf", r["Content-Type"]
    assert r.content[:4] == b"%PDF", "response is not a valid PDF"
    print(f"  export: 200  pdf bytes={len(r.content)}")

    print("\nAll smoke-test steps passed.")


if __name__ == "__main__":
    main()
