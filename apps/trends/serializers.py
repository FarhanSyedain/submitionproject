from rest_framework import serializers

from apps.trends.models import Trend


class TrendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trend
        fields = "__all__"
        read_only_fields = ("id", "created_at", "session", "business")
