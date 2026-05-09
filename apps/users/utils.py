"""Helpers for resolving the current user across authenticated and dev requests."""
from django.contrib.auth import get_user_model

DEMO_USERNAME = "demo"


def get_or_create_demo_user():
    """Return a stable 'demo' user used when the request is unauthenticated.

    Convenience for early development so we can hit the API without first
    standing up the auth flow. Once auth is enforced (production settings),
    `resolve_user` will always return the authenticated user instead.
    """
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username=DEMO_USERNAME,
        defaults={
            "email": "demo@zeaniv.local",
            "full_name": "Demo User",
        },
    )
    return user


def resolve_user(request):
    if request.user.is_authenticated:
        return request.user
    return get_or_create_demo_user()
