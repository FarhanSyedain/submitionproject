from rest_framework import serializers

from apps.reports.models import Report


class ReportSerializer(serializers.ModelSerializer):
    ks_audio_available = serializers.SerializerMethodField()

    class Meta:
        model = Report
        # Explicit list — we never want the raw `ks_audio` BinaryField
        # serialised into JSON (it'd balloon the payload). The frontend
        # streams it via the audio endpoint instead.
        fields = (
            "id",
            "session",
            "business",
            "user",
            "title",
            "executive_summary",
            "top_ideas",
            "key_insights",
            "recommended_actions",
            "pdf_url",
            "created_at",
            "ks_translation",
            "ks_audio_text",
            "ks_audio_available",
            "ks_audio_content_type",
            "localization_status",
            "localization_error",
        )
        read_only_fields = (
            "id",
            "created_at",
            "session",
            "business",
            "user",
            "ks_audio_available",
        )

    def get_ks_audio_available(self, obj) -> bool:
        return bool(obj.ks_audio)
