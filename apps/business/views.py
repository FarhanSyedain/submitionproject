from rest_framework import viewsets

from apps.business.models import BusinessProfile
from apps.business.serializers import BusinessProfileSerializer
from apps.users.utils import resolve_user


class BusinessProfileViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessProfileSerializer
    lookup_field = "pk"

    def get_queryset(self):
        user = resolve_user(self.request)
        return BusinessProfile.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=resolve_user(self.request))
