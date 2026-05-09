import uuid

from django.db import models


class Idea(models.Model):
    CATEGORY_CHOICES = [
        ("product", "Product"),
        ("service", "Service"),
        ("marketing", "Marketing"),
        ("operations", "Operations"),
        ("partnership", "Partnership"),
        ("revenue_stream", "Revenue Stream"),
    ]

    SOURCE_CHOICES = [
        ("ai_generated", "AI Generated"),
        ("trend_based", "Trend Based"),
        ("feedback_derived", "Feedback Derived"),
        ("competitor_gap", "Competitor Gap"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        "analysis.AnalysisSession",
        on_delete=models.CASCADE,
        related_name="ideas",
    )
    business = models.ForeignKey(
        "business.BusinessProfile",
        on_delete=models.CASCADE,
        related_name="ideas",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, blank=True)
    source = models.CharField(
        max_length=50, choices=SOURCE_CHOICES, default="ai_generated"
    )

    feasibility_score = models.SmallIntegerField(null=True, blank=True)  # 1–10
    market_fit_score = models.SmallIntegerField(null=True, blank=True)
    effort_score = models.SmallIntegerField(null=True, blank=True)
    roi_score = models.SmallIntegerField(null=True, blank=True)
    overall_score = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )

    time_to_implement = models.CharField(max_length=50, blank=True)
    required_resources = models.JSONField(default=list, blank=True)
    risks = models.JSONField(default=list, blank=True)
    next_steps = models.JSONField(default=list, blank=True)

    is_saved = models.BooleanField(default=False)
    user_rating = models.SmallIntegerField(null=True, blank=True)  # 1–5 stars
    user_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ideas"
        indexes = [
            models.Index(fields=["session"], name="idx_ideas_session"),
            models.Index(fields=["-overall_score"], name="idx_ideas_score"),
            models.Index(fields=["category"], name="idx_ideas_category"),
            models.Index(
                fields=["is_saved"],
                name="idx_ideas_saved",
                condition=models.Q(is_saved=True),
            ),
        ]
        ordering = ["-overall_score", "-created_at"]

    def __str__(self) -> str:
        return self.title


class IdeaValidation(models.Model):
    COMPETITION_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("saturated", "Saturated"),
    ]

    VERDICT_CHOICES = [
        ("strong_yes", "Strong Yes"),
        ("yes", "Yes"),
        ("maybe", "Maybe"),
        ("no", "No"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    idea = models.OneToOneField(
        Idea, on_delete=models.CASCADE, related_name="validation"
    )
    session = models.ForeignKey(
        "analysis.AnalysisSession",
        on_delete=models.CASCADE,
        related_name="validations",
    )
    market_size = models.CharField(max_length=100, blank=True)
    target_customer = models.TextField(blank=True)
    problem_severity = models.SmallIntegerField(null=True, blank=True)  # 1–10
    solution_uniqueness = models.SmallIntegerField(null=True, blank=True)
    competition_level = models.CharField(
        max_length=20, choices=COMPETITION_CHOICES, blank=True
    )
    monetization_model = models.CharField(max_length=100, blank=True)
    revenue_potential = models.CharField(max_length=100, blank=True)
    go_to_market = models.TextField(blank=True)
    key_risks = models.JSONField(default=list, blank=True)
    validation_summary = models.TextField(blank=True)
    verdict = models.CharField(max_length=20, choices=VERDICT_CHOICES, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "idea_validations"
        indexes = [models.Index(fields=["idea"], name="idx_validations_idea")]
        ordering = ["-created_at"]
