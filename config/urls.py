"""Root URL configuration."""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def healthz(_request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    path("api/auth/", include("apps.users.urls")),
    path("api/businesses/", include("apps.business.urls")),
    path("api/analysis/", include("apps.analysis.urls")),
    path("api/ideas/", include("apps.ideas.urls")),
]
