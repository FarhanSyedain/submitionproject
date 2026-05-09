from rest_framework import serializers

from apps.feedback.models import FeedbackInsight, FeedbackSubmission


class FeedbackInsightSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackInsight
        fields = "__all__"
        read_only_fields = ("id", "created_at", "submission")


class FeedbackSubmissionSerializer(serializers.ModelSerializer):
    insights = FeedbackInsightSerializer(many=True, read_only=True)

    class Meta:
        model = FeedbackSubmission
        fields = (
            "id",
            "session",
            "business",
            "raw_text",
            "source_type",
            "created_at",
            "insights",
        )
        read_only_fields = ("id", "created_at", "session", "business", "insights")


class FeedbackSubmitSerializer(serializers.Serializer):
    """Input for POST /api/analysis/{id}/feedback/submit/"""

    raw_text = serializers.CharField()
    source_type = serializers.ChoiceField(
        choices=FeedbackSubmission.SOURCE_CHOICES,
        default="manual",
        required=False,
    )
