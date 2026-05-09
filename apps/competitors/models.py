import uuid

from django.db import models


class Competitor(models.Model):
    POSITION_CHOICES = [
        ("leader", "Leader"),
        ("challenger", "Challenger"),
        ("niche", "Niche"),
        ("new", "New"),
    ]

    SIZE_CHOICES = [
        ("startup", "Startup"),
        ("smb", "SMB"),
        ("enterprise", "Enterprise"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        "analysis.AnalysisSession",
        on_delete=models.CASCADE,
        related_name="competitors",
    )
    business = models.ForeignKey(
        "business.BusinessProfile",
        on_delete=models.CASCADE,
        related_name="competitors",
    )
    name = models.CharField(max_length=255)
    website = models.CharField(max_length=500, blank=True)
    description = models.TextField(blank=True)
    strengths = models.JSONField(default=list, blank=True)
    weaknesses = models.JSONField(default=list, blank=True)
    market_position = models.CharField(
        max_length=100, choices=POSITION_CHOICES, blank=True
    )
    estimated_size = models.CharField(
        max_length=100, choices=SIZE_CHOICES, blank=True
    )
    threat_level = models.SmallIntegerField(default=3)  # 1–5
    opportunity_gap = models.TextField(blank=True)
    source_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "competitors"
        indexes = [models.Index(fields=["session"], name="idx_competitors_session")]
        ordering = ["-threat_level", "name"]

    def __str__(self) -> str:
        return self.name
