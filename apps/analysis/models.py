import uuid

from django.conf import settings
from django.db import models


class AnalysisSession(models.Model):
    """One full Zeaniv run for a business profile."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    PROVIDER_CHOICES = [
        ("ollama", "Ollama"),
        ("gemini", "Gemini"),
        ("mock", "Mock"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    business = models.ForeignKey(
        "business.BusinessProfile",
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analysis_sessions",
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")
    llm_provider = models.CharField(
        max_length=30, choices=PROVIDER_CHOICES, default="ollama"
    )
    llm_model = models.CharField(
        max_length=100, default="qwen3:30b-a3b-instruct-2507-q4_K_M"
    )
    total_tokens = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Per-module status — lets the UI show progress while the session runs.
    # Each value is one of: pending | running | completed | failed
    module_status = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "analysis_sessions"
        indexes = [
            models.Index(fields=["business"], name="idx_sessions_business"),
            models.Index(fields=["user"], name="idx_sessions_user"),
            models.Index(fields=["status"], name="idx_sessions_status"),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Session {self.id} ({self.status})"


class LlmLog(models.Model):
    """Per-call LLM telemetry: tokens, latency, errors."""

    PROVIDER_CHOICES = AnalysisSession.PROVIDER_CHOICES

    MODULE_CHOICES = [
        ("competitor", "Competitor"),
        ("feedback", "Feedback"),
        ("ideation", "Ideation"),
        ("trends", "Trends"),
        ("validation", "Validation"),
        ("report", "Report"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        AnalysisSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="llm_logs",
    )
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES)
    model = models.CharField(max_length=100)
    module = models.CharField(max_length=50, choices=MODULE_CHOICES)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    latency_ms = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=True)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "llm_logs"
        indexes = [models.Index(fields=["session"], name="idx_llm_logs_session")]
        ordering = ["-created_at"]
