from django.urls import path

from apps.analysis.views import (
    CompetitorListView,
    FeedbackListView,
    FeedbackSubmitView,
    IdeaListView,
    ReportAudioView,
    ReportDetailView,
    ReportExportView,
    ReportTranslateView,
    SessionDetailView,
    SessionListView,
    SessionRerunView,
    SessionStatusView,
    StartAnalysisView,
    TrendListView,
    ValidationListView,
)

urlpatterns = [
    path("", SessionListView.as_view(), name="analysis-list"),
    path("start/", StartAnalysisView.as_view(), name="analysis-start"),
    path("<uuid:pk>/", SessionDetailView.as_view(), name="analysis-detail"),
    path("<uuid:pk>/status/", SessionStatusView.as_view(), name="analysis-status"),
    path("<uuid:pk>/rerun/", SessionRerunView.as_view(), name="analysis-rerun"),
    path(
        "<uuid:session_id>/competitors/",
        CompetitorListView.as_view(),
        name="analysis-competitors",
    ),
    path(
        "<uuid:session_id>/feedback/",
        FeedbackListView.as_view(),
        name="analysis-feedback",
    ),
    path(
        "<uuid:session_id>/feedback/submit/",
        FeedbackSubmitView.as_view(),
        name="analysis-feedback-submit",
    ),
    path(
        "<uuid:session_id>/ideas/",
        IdeaListView.as_view(),
        name="analysis-ideas",
    ),
    path(
        "<uuid:session_id>/trends/",
        TrendListView.as_view(),
        name="analysis-trends",
    ),
    path(
        "<uuid:session_id>/validation/",
        ValidationListView.as_view(),
        name="analysis-validation",
    ),
    path(
        "<uuid:session_id>/report/",
        ReportDetailView.as_view(),
        name="analysis-report",
    ),
    path(
        "<uuid:session_id>/report/export/",
        ReportExportView.as_view(),
        name="analysis-report-export",
    ),
    path(
        "<uuid:session_id>/report/translate/",
        ReportTranslateView.as_view(),
        name="analysis-report-translate",
    ),
    path(
        "<uuid:session_id>/report/audio/",
        ReportAudioView.as_view(),
        name="analysis-report-audio",
    ),
]
