import uuid

from django.conf import settings
from django.db import models


class Report(models.Model):
    """Final exportable summary tying together all module outputs."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(
        "analysis.AnalysisSession",
        on_delete=models.CASCADE,
        related_name="report",
    )
    business = models.ForeignKey(
        "business.BusinessProfile",
        on_delete=models.CASCADE,
        related_name="reports",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reports",
    )
    title = models.CharField(max_length=255, blank=True)
    executive_summary = models.TextField(blank=True)
    top_ideas = models.JSONField(default=list, blank=True)  # list of idea IDs
    key_insights = models.JSONField(default=list, blank=True)
    recommended_actions = models.JSONField(default=list, blank=True)
    pdf_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ── Cached Kashmiri localisation ────────────────────────────────────
    # Populated automatically by the post-pipeline localiser so reopening
    # an old session is instant (no re-translate, no re-synthesise).
    ks_translation = models.JSONField(default=dict, blank=True)
    ks_audio_text = models.TextField(blank=True)
    ks_audio = models.BinaryField(blank=True, null=True)
    ks_audio_content_type = models.CharField(max_length=64, blank=True)
    localization_status = models.CharField(
        max_length=20, default="pending", blank=True
    )  # pending | running | completed | failed | skipped
    localization_error = models.TextField(blank=True)

    class Meta:
        db_table = "reports"
        indexes = [
            models.Index(fields=["session"], name="idx_reports_session"),
            models.Index(fields=["user"], name="idx_reports_user"),
        ]
        ordering = ["-created_at"]
