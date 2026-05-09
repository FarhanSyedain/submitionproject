from rest_framework import serializers

from apps.competitors.models import Competitor


class CompetitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Competitor
        fields = "__all__"
        read_only_fields = ("id", "created_at", "session", "business")
