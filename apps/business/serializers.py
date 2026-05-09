from rest_framework import serializers

from apps.business.models import BusinessProfile


class BusinessProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessProfile
        fields = (
            "id",
            "name",
            "description",
            "industry",
            "target_market",
            "location",
            "stage",
            "website_url",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")
