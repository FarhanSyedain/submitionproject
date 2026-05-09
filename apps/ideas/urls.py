from django.urls import path

from apps.ideas.views import IdeaDetailView

urlpatterns = [
    path("<uuid:pk>/", IdeaDetailView.as_view(), name="idea-detail"),
]
