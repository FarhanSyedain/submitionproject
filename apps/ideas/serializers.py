from rest_framework import serializers

from apps.ideas.models import Idea, IdeaValidation


class IdeaValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdeaValidation
        fields = "__all__"
        read_only_fields = ("id", "created_at", "session", "idea")


class IdeaSerializer(serializers.ModelSerializer):
    validation = IdeaValidationSerializer(read_only=True)

    class Meta:
        model = Idea
        fields = (
            "id",
            "session",
            "business",
            "title",
            "description",
            "category",
            "source",
            "feasibility_score",
            "market_fit_score",
            "effort_score",
            "roi_score",
            "overall_score",
            "time_to_implement",
            "required_resources",
            "risks",
            "next_steps",
            "is_saved",
            "user_rating",
            "user_notes",
            "created_at",
            "updated_at",
            "validation",
        )
        read_only_fields = (
            "id",
            "session",
            "business",
            "title",
            "description",
            "category",
            "source",
            "feasibility_score",
            "market_fit_score",
            "effort_score",
            "roi_score",
            "overall_score",
            "time_to_implement",
            "required_resources",
            "risks",
            "next_steps",
            "created_at",
            "updated_at",
            "validation",
        )
        # Writable on PATCH: is_saved, user_rating, user_notes.
