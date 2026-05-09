from rest_framework.routers import DefaultRouter

from apps.business.views import BusinessProfileViewSet

router = DefaultRouter()
router.register(r"", BusinessProfileViewSet, basename="business")

urlpatterns = router.urls
