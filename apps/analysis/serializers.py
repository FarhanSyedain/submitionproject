from rest_framework import serializers

from apps.analysis.models import AnalysisSession


class AnalysisSessionSerializer(serializers.ModelSerializer):
    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = AnalysisSession
        fields = (
            "id",
            "business",
            "business_name",
            "user",
            "status",
            "llm_provider",
            "llm_model",
            "module_status",
            "total_tokens",
            "error_message",
            "started_at",
            "completed_at",
            "created_at",
        )
        read_only_fields = fields


class AnalysisStartSerializer(serializers.Serializer):
    business_id = serializers.UUIDField()
    llm_provider = serializers.ChoiceField(
        choices=AnalysisSession.PROVIDER_CHOICES,
        required=False,
        allow_blank=True,
    )


class AnalysisStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnalysisSession
        fields = (
            "id",
            "status",
            "module_status",
            "total_tokens",
            "started_at",
            "completed_at",
            "error_message",
        )
        read_only_fields = fields
