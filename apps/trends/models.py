import uuid

from django.db import models


class Trend(models.Model):
    TYPE_CHOICES = [
        ("technology", "Technology"),
        ("consumer_behavior", "Consumer Behavior"),
        ("regulation", "Regulation"),
        ("market", "Market"),
        ("social", "Social"),
    ]

    MOMENTUM_CHOICES = [
        ("emerging", "Emerging"),
        ("rising", "Rising"),
        ("peaking", "Peaking"),
        ("declining", "Declining"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        "analysis.AnalysisSession",
        on_delete=models.CASCADE,
        related_name="trends",
    )
    business = models.ForeignKey(
        "business.BusinessProfile",
        on_delete=models.CASCADE,
        related_name="trends",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    trend_type = models.CharField(max_length=50, choices=TYPE_CHOICES, blank=True)
    momentum = models.CharField(
        max_length=20, choices=MOMENTUM_CHOICES, default="rising"
    )
    relevance_score = models.SmallIntegerField(null=True, blank=True)  # 1–10
    opportunity = models.TextField(blank=True)
    threat = models.TextField(blank=True)
    source_urls = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "trends"
        indexes = [
            models.Index(fields=["session"], name="idx_trends_session"),
            models.Index(fields=["-relevance_score"], name="idx_trends_relevance"),
        ]
        ordering = ["-relevance_score", "-created_at"]

    def __str__(self) -> str:
        return self.title
