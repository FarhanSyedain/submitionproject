import uuid

from django.conf import settings
from django.db import models


class BusinessProfile(models.Model):
    STAGE_CHOICES = [
        ("idea", "Idea"),
        ("startup", "Startup"),
        ("growth", "Growth"),
        ("enterprise", "Enterprise"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_profiles",
    )
    name = models.CharField(max_length=255)
    description = models.TextField()
    industry = models.CharField(max_length=100, blank=True)
    target_market = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    stage = models.CharField(max_length=50, choices=STAGE_CHOICES, default="idea")
    website_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "business_profiles"
        indexes = [models.Index(fields=["user"], name="idx_business_profiles_user")]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.name
