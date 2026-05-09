"""Development overrides."""
from .base import *  # noqa: F401,F403

DEBUG = True

# Allow any host in dev so Django's test Client (host=testserver) works
# alongside localhost browser requests. Tighten in production.
ALLOWED_HOSTS = ["*"]

# Loosen CORS for local dev so Vite (any port) can hit the API.
CORS_ALLOW_ALL_ORIGINS = True

# Allow unauthenticated access during early dev so we can poke the API
# without first standing up the auth flow. Tighten this once auth is wired.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.AllowAny",
    ),
}

# Surface TTS + localisation INFO logs in the dev console — useful for
# watching Matcha synth timings and Modal hits/responses live.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "concise": {
            "format": "%(asctime)s %(levelname)-5s %(name)s %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "concise",
        },
    },
    "loggers": {
        "services.tts": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "apps.reports.localization": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
