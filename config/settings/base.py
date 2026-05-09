"""Base settings shared across all environments."""
from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    USE_DJANGO_Q=(bool, False),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 60),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
)

# Read .env if present (development convenience).
env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env(
    "SECRET_KEY",
    default="dev-secret-change-me-this-is-only-for-local-development-not-prod",
)
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ── Applications ─────────────────────────────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "django_q",
]

LOCAL_APPS = [
    "apps.users",
    "apps.business",
    "apps.analysis",
    "apps.competitors",
    "apps.feedback",
    "apps.ideas",
    "apps.trends",
    "apps.reports",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = "users.User"

# ── Middleware ───────────────────────────────────────────────────────────
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Database ─────────────────────────────────────────────────────────────
# Default to SQLite; honor DATABASE_URL if set (e.g. postgres in prod).
DATABASES = {
    "default": env.db_url(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Password validation ──────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ── i18n ─────────────────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static & media ───────────────────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── DRF ──────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env("JWT_ACCESS_TOKEN_LIFETIME_MINUTES")),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env("JWT_REFRESH_TOKEN_LIFETIME_DAYS")),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ── CORS ─────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"]
)
CORS_ALLOW_CREDENTIALS = True

# ── LLM provider config (consumed by services.llm.router) ───────────────
LLM_PROVIDER = env("LLM_PROVIDER", default="ollama")  # ollama | gemini | mock
OLLAMA_BASE_URL = env("OLLAMA_BASE_URL", default="http://localhost:11434")
OLLAMA_MODEL = env("OLLAMA_MODEL", default="llama3.2")
GEMINI_API_KEY = env("GEMINI_API_KEY", default="")
GEMINI_MODEL = env("GEMINI_MODEL", default="gemini-2.5-flash")

# ── External APIs ────────────────────────────────────────────────────────
SERPAPI_KEY = env("SERPAPI_KEY", default="")
NEWS_API_KEY = env("NEWS_API_KEY", default="")

# ── Translation ──────────────────────────────────────────────────────────
# llm         — uses the configured LLM client (works out of the box)
# huggingface — loads a local HF Transformers model (en↔ks; needs torch)
# local_http  — POSTs to TRANSLATION_URL with a configurable JSON shape
TRANSLATION_PROVIDER = env("TRANSLATION_PROVIDER", default="llm")
TRANSLATION_URL = env("TRANSLATION_URL", default="")
TRANSLATION_TEXT_FIELD = env("TRANSLATION_TEXT_FIELD", default="text")
TRANSLATION_TARGET_FIELD = env("TRANSLATION_TARGET_FIELD", default="target_lang")
TRANSLATION_SOURCE_FIELD = env("TRANSLATION_SOURCE_FIELD", default="source_lang")
TRANSLATION_RESPONSE_FIELD = env("TRANSLATION_RESPONSE_FIELD", default="translation")

# Hugging Face translator config (used when TRANSLATION_PROVIDER=huggingface).
HF_TRANSLATION_MODEL = env(
    "HF_TRANSLATION_MODEL", default="Omarrran/koshur-kouter-ks-en_v1"
)
HF_TRANSLATION_MAX_NEW_TOKENS = env.int("HF_TRANSLATION_MAX_NEW_TOKENS", default=256)
HF_TRANSLATION_DTYPE = env("HF_TRANSLATION_DTYPE", default="bfloat16")

# ── TTS ──────────────────────────────────────────────────────────────────
TTS_PROVIDER = env("TTS_PROVIDER", default="local_http")
TTS_URL = env("TTS_URL", default="")
TTS_TEXT_FIELD = env("TTS_TEXT_FIELD", default="text")
TTS_LANG_FIELD = env("TTS_LANG_FIELD", default="lang")  # set to "" to omit
TTS_STEPS_FIELD = env("TTS_STEPS_FIELD", default="n_timesteps")  # set to "" to omit
TTS_AUDIO_FIELD = env("TTS_AUDIO_FIELD", default="audio")
TTS_AUTH_BEARER = env("TTS_AUTH_BEARER", default="")
# Cap diffusion steps for the local_http (Modal) provider — the deployed
# endpoint validates n_timesteps <= 500 and gets sluggish above ~150.
# Local Matcha is unaffected.
TTS_HTTP_MAX_STEPS = env.int("TTS_HTTP_MAX_STEPS", default=150)

# Local in-process Matcha-TTS (TTS_PROVIDER=local_matcha). Loads a Bolbosh
# checkpoint directly — no Modal, no HTTP hop. Requires torch + soundfile +
# the Bolbosh fork of matcha-tts on the import path.
TTS_LOCAL_CKPT_PATH = env("TTS_LOCAL_CKPT_PATH", default="/Users/farhan/klm/model.ckpt")
TTS_LOCAL_VOCODER_PATH = env("TTS_LOCAL_VOCODER_PATH", default="")  # blank → next to ckpt
TTS_LOCAL_BOLBOSH_PATH = env("TTS_LOCAL_BOLBOSH_PATH", default="/Users/farhan/klm/Bolbosh")
TTS_LOCAL_DEVICE = env("TTS_LOCAL_DEVICE", default="auto")  # auto | cpu | cuda | mps
TTS_LOCAL_SPEAKER_ID = env.int("TTS_LOCAL_SPEAKER_ID", default=423)
TTS_LOCAL_SPEAKING_RATE = env.float("TTS_LOCAL_SPEAKING_RATE", default=1.0)
TTS_LOCAL_N_TIMESTEPS = env.int("TTS_LOCAL_N_TIMESTEPS", default=20)

# Diffusion steps for the executive-summary narration — used by the
# auto-localiser AND the user-driven regenerate. Local Matcha takes the
# full value (1500 for the demo); the Modal client clamps internally to
# TTS_HTTP_MAX_STEPS, so we don't need a second knob here.
TTS_NUM_STEPS = env.int("TTS_NUM_STEPS", default=1500)

# ── Model swap ───────────────────────────────────────────────────────────
# When True, services.memory will unload the *other* model before each
# request — i.e. analysis frees the HF translator's memory, translation
# tells Ollama to release its weights. Necessary on machines that can't
# hold both qwen3:30b (~18GB) and koshur-kouter (~2.5GB) at the same time.
ENABLE_MODEL_SWAP = env.bool("ENABLE_MODEL_SWAP", default=True)

# ── Async runner ─────────────────────────────────────────────────────────
USE_DJANGO_Q = env("USE_DJANGO_Q")

# Django Q config — ORM broker keeps things simple (no Redis required).
Q_CLUSTER = {
    "name": "zeaniv",
    "workers": 2,
    "recycle": 500,
    "timeout": 600,
    "retry": 900,
    "compress": True,
    "save_limit": 250,
    "queue_limit": 500,
    "cpu_affinity": 1,
    "label": "Django Q",
    "orm": "default",
}
