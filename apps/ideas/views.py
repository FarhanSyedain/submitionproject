from rest_framework import generics

from apps.ideas.models import Idea
from apps.ideas.serializers import IdeaSerializer


class IdeaDetailView(generics.RetrieveUpdateAPIView):
    """GET / PATCH /api/ideas/{id}/

    Only `is_saved`, `user_rating`, and `user_notes` are writable
    (enforced via the serializer's read_only_fields).
    """

    queryset = Idea.objects.all()
    serializer_class = IdeaSerializer
    lookup_field = "pk"
