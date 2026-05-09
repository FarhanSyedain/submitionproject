import uuid

from django.db import models


class FeedbackSubmission(models.Model):
    SOURCE_CHOICES = [
        ("manual", "Manual"),
        ("google_reviews", "Google Reviews"),
        ("reddit", "Reddit"),
        ("twitter", "Twitter"),
        ("support_tickets", "Support Tickets"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        "analysis.AnalysisSession",
        on_delete=models.CASCADE,
        related_name="feedback_submissions",
    )
    business = models.ForeignKey(
        "business.BusinessProfile",
        on_delete=models.CASCADE,
        related_name="feedback_submissions",
    )
    raw_text = models.TextField()
    source_type = models.CharField(
        max_length=50, choices=SOURCE_CHOICES, default="manual"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feedback_submissions"
        indexes = [models.Index(fields=["session"], name="idx_feedback_session")]
        ordering = ["-created_at"]


class FeedbackInsight(models.Model):
    INSIGHT_TYPE_CHOICES = [
        ("pain_point", "Pain Point"),
        ("feature_request", "Feature Request"),
        ("compliment", "Compliment"),
        ("bug", "Bug"),
        ("question", "Question"),
    ]

    SENTIMENT_CHOICES = [
        ("positive", "Positive"),
        ("neutral", "Neutral"),
        ("negative", "Negative"),
    ]

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    submission = models.ForeignKey(
        FeedbackSubmission,
        on_delete=models.CASCADE,
        related_name="insights",
    )
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    frequency_score = models.SmallIntegerField(default=1)  # 1–10
    sentiment = models.CharField(
        max_length=20, choices=SENTIMENT_CHOICES, default="neutral"
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )
    example_quotes = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "feedback_insights"
        indexes = [
            models.Index(fields=["submission"], name="idx_insights_submission"),
            models.Index(fields=["insight_type"], name="idx_insights_type"),
        ]
        ordering = ["-frequency_score", "-created_at"]
