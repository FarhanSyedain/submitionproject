from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.analysis.models import AnalysisSession
from apps.analysis.serializers import (
    AnalysisSessionSerializer,
    AnalysisStartSerializer,
    AnalysisStatusSerializer,
)
from apps.analysis.tasks import enqueue_analysis_session
from apps.business.models import BusinessProfile
from apps.competitors.models import Competitor
from apps.competitors.serializers import CompetitorSerializer
from apps.feedback.models import FeedbackSubmission
from apps.feedback.serializers import (
    FeedbackSubmissionSerializer,
    FeedbackSubmitSerializer,
)
from apps.ideas.models import Idea, IdeaValidation
from apps.ideas.serializers import IdeaSerializer, IdeaValidationSerializer
from apps.reports.models import Report
from apps.reports.serializers import ReportSerializer
from apps.trends.models import Trend
from apps.trends.serializers import TrendSerializer
from apps.users.utils import resolve_user


# ── Session lifecycle ───────────────────────────────────────────────────
class StartAnalysisView(APIView):
    """POST /api/analysis/start/

    Body: {"business_id": "<uuid>", "llm_provider": "ollama|gemini|mock"}
    Creates a session and runs (or enqueues) the agent pipeline.
    """

    def post(self, request):
        serializer = AnalysisStartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = resolve_user(request)
        business = get_object_or_404(
            BusinessProfile, pk=serializer.validated_data["business_id"], user=user
        )

        provider = serializer.validated_data.get("llm_provider") or ""
        session = AnalysisSession.objects.create(
            business=business,
            user=user,
            llm_provider=provider or "mock",
            module_status={
                "competitor": "pending",
                "trends": "pending",
                "ideation": "pending",
                "validation": "pending",
                "report": "pending",
            },
        )
        enqueue_analysis_session(str(session.id))

        # Re-read so we get the (possibly already-completed) status when sync.
        session.refresh_from_db()
        return Response(
            AnalysisSessionSerializer(session).data, status=status.HTTP_201_CREATED
        )


class SessionListView(generics.ListAPIView):
    """GET /api/analysis/ — sessions belonging to the current user."""

    serializer_class = AnalysisSessionSerializer

    def get_queryset(self):
        user = resolve_user(self.request)
        return AnalysisSession.objects.filter(user=user).select_related("business")


class SessionDetailView(generics.RetrieveAPIView):
    """GET /api/analysis/{id}/"""

    queryset = AnalysisSession.objects.all()
    serializer_class = AnalysisSessionSerializer
    lookup_field = "pk"


class SessionStatusView(generics.RetrieveAPIView):
    """GET /api/analysis/{id}/status/ — lightweight polling endpoint."""

    queryset = AnalysisSession.objects.all()
    serializer_class = AnalysisStatusSerializer
    lookup_field = "pk"


class SessionRerunView(APIView):
    """POST /api/analysis/{id}/rerun/

    Re-runs the full pipeline. Existing rows for this session are deleted
    so we don't end up with duplicate competitors / ideas / etc.
    """

    def post(self, request, pk):
        session = get_object_or_404(AnalysisSession, pk=pk)
        Competitor.objects.filter(session=session).delete()
        Trend.objects.filter(session=session).delete()
        Idea.objects.filter(session=session).delete()  # cascades to IdeaValidation
        Report.objects.filter(session=session).delete()
        # Feedback submissions are user-supplied, leave them alone.

        enqueue_analysis_session(str(session.id))
        session.refresh_from_db()
        return Response(AnalysisSessionSerializer(session).data)


# ── Module read endpoints ───────────────────────────────────────────────
class _SessionScopedListView(generics.ListAPIView):
    """Filter a queryset by the session_id URL kwarg."""

    session_field = "session_id"

    def get_queryset(self):  # noqa: D401
        return self.queryset.filter(**{self.session_field: self.kwargs["session_id"]})


class CompetitorListView(_SessionScopedListView):
    queryset = Competitor.objects.all()
    serializer_class = CompetitorSerializer


class TrendListView(_SessionScopedListView):
    queryset = Trend.objects.all()
    serializer_class = TrendSerializer


class IdeaListView(_SessionScopedListView):
    queryset = Idea.objects.select_related("validation").all()
    serializer_class = IdeaSerializer


class ValidationListView(_SessionScopedListView):
    queryset = IdeaValidation.objects.all()
    serializer_class = IdeaValidationSerializer


class FeedbackListView(_SessionScopedListView):
    queryset = FeedbackSubmission.objects.prefetch_related("insights").all()
    serializer_class = FeedbackSubmissionSerializer


class FeedbackSubmitView(APIView):
    """POST /api/analysis/{session_id}/feedback/submit/

    Stores a raw feedback blob and runs the FeedbackAgent inline so the
    insights come back in the same response.
    """

    def post(self, request, session_id):
        session = get_object_or_404(AnalysisSession, pk=session_id)
        serializer = FeedbackSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        submission = FeedbackSubmission.objects.create(
            session=session,
            business=session.business,
            raw_text=serializer.validated_data["raw_text"],
            source_type=serializer.validated_data.get("source_type", "manual"),
        )

        from services.llm import get_llm_client
        from services.memory import unload_translator
        from services.modules import FeedbackAgent

        # Feedback analysis uses the LLM, so free the HF translator first.
        unload_translator()
        client = get_llm_client(session.llm_provider)
        try:
            FeedbackAgent(submission, client).run()
        except Exception as exc:
            return Response(
                {
                    "detail": f"Feedback analysis failed: {exc}",
                    "submission_id": str(submission.id),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        submission.refresh_from_db()
        return Response(
            FeedbackSubmissionSerializer(submission).data,
            status=status.HTTP_201_CREATED,
        )


class ReportDetailView(APIView):
    """GET /api/analysis/{session_id}/report/"""

    def get(self, request, session_id):
        report = get_object_or_404(Report, session_id=session_id)
        return Response(ReportSerializer(report).data)


class ReportExportView(APIView):
    """POST /api/analysis/{session_id}/report/export/

    Renders the report to PDF and streams it back as an attachment.
    """

    def post(self, request, session_id):
        report = get_object_or_404(Report, session_id=session_id)

        from django.http import HttpResponse

        from services.pdf.report_pdf import render_report_pdf

        pdf_bytes = render_report_pdf(report)
        filename = f"zeaniv-report-{report.business.name}.pdf".replace(" ", "_")
        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["Content-Length"] = str(len(pdf_bytes))
        return response


class ReportTranslateView(APIView):
    """POST /api/analysis/{session_id}/report/translate/

    Body: {"lang": "ks"}  (defaults to Kashmiri)
    Returns the translated executive summary, key insights, and
    recommended-action labels alongside the original.

    Kashmiri hits a per-report cache (`Report.ks_translation`) populated by
    the post-pipeline localiser, so reopening a previous session is instant.
    """

    def post(self, request, session_id):
        from services.memory import unload_llm
        from services.translation import get_translator
        from services.translation.base import LANGUAGES

        report = get_object_or_404(Report, session_id=session_id)
        lang = (request.data.get("lang") or "ks").lower()
        if lang not in LANGUAGES:
            return Response(
                {"detail": f"Unsupported language: {lang}", "supported": list(LANGUAGES)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cache hit — return the pre-warmed Kashmiri payload immediately.
        if lang == "ks" and report.ks_translation:
            return Response(report.ks_translation)

        # Free up memory held by Ollama before loading the HF translator.
        unload_llm()

        translator = get_translator()

        # Batch the strings we need translated so each provider can decide
        # whether to dispatch them individually or as one call.
        actions = report.recommended_actions or []
        texts = [
            report.executive_summary or "",
            *(report.key_insights or []),
            *[a.get("action", "") for a in actions],
        ]
        try:
            translated = translator.translate_many(
                texts, target_lang=lang, source_lang="en"
            )
        except Exception as exc:
            return Response(
                {"detail": f"Translation failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        idx = 0
        out_summary = translated[idx] if texts[idx] else ""
        idx += 1
        out_insights = []
        for original in (report.key_insights or []):
            out_insights.append(translated[idx] if original else "")
            idx += 1
        out_actions = []
        for original in actions:
            translated_action = translated[idx] if original.get("action") else ""
            idx += 1
            out_actions.append({**original, "action": translated_action})

        payload = {
            "lang": lang,
            "language": LANGUAGES[lang],
            "provider": translator.provider,
            "executive_summary": out_summary,
            "key_insights": out_insights,
            "recommended_actions": out_actions,
        }

        # Persist Kashmiri so subsequent opens hit the cache.
        if lang == "ks":
            report.ks_translation = payload
            report.save(update_fields=["ks_translation"])

        return Response(payload)


class ReportAudioView(APIView):
    """POST or GET /api/analysis/{session_id}/report/audio/

    Body (POST): {"lang": "ks", "section": "executive_summary"|"all"}
    Synthesises Kashmiri speech from the requested section of the report.
    The executive-summary narration is pre-warmed by the post-pipeline
    localiser, so the common case is a cache hit and no TTS call.

    GET serves the cached Kashmiri executive-summary narration.
    """

    def get(self, request, session_id):
        from django.http import HttpResponse

        report = get_object_or_404(Report, session_id=session_id)
        if not report.ks_audio:
            return Response(
                {"detail": "No cached narration; synthesise via POST."},
                status=status.HTTP_404_NOT_FOUND,
            )
        response = HttpResponse(
            bytes(report.ks_audio),
            content_type=report.ks_audio_content_type or "audio/wav",
        )
        response["Cache-Control"] = "private, max-age=86400"
        return response

    def post(self, request, session_id):
        from django.conf import settings
        from django.http import HttpResponse

        from services.memory import unload_llm
        from services.translation import get_translator
        from services.translation.base import LANGUAGES
        from services.tts import get_tts

        report = get_object_or_404(Report, session_id=session_id)
        lang = (request.data.get("lang") or "ks").lower()
        if lang not in LANGUAGES:
            return Response(
                {"detail": f"Unsupported language: {lang}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        section = (request.data.get("section") or "executive_summary").lower()
        # Per-request overrides — the report tab uses these to flip between
        # local Matcha and the Modal HTTP gateway and to force a re-synth.
        provider_override = (request.data.get("provider") or "").strip() or None
        force = bool(request.data.get("force"))

        # Cache hit — Kashmiri executive-summary narration only, and only
        # when the caller didn't explicitly ask us to regenerate.
        if (
            not force
            and lang == "ks"
            and section == "executive_summary"
            and report.ks_audio
        ):
            response = HttpResponse(
                bytes(report.ks_audio),
                content_type=report.ks_audio_content_type or "audio/wav",
            )
            response["Cache-Control"] = "private, max-age=86400"
            return response

        # Build the source text in English…
        if section == "executive_summary":
            source = report.executive_summary or ""
        elif section == "key_insights":
            source = "\n".join(report.key_insights or [])
        elif section == "all":
            parts = [report.executive_summary or ""]
            parts += list(report.key_insights or [])
            parts += [a.get("action", "") for a in (report.recommended_actions or [])]
            source = "\n\n".join(p for p in parts if p)
        else:
            return Response(
                {"detail": f"Unknown section: {section}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not source.strip():
            return Response(
                {"detail": "Nothing to synthesise — the report section is empty."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # …translate it (skip if target is English). Re-use the cached
        # Kashmiri executive-summary translation when we have it — saves
        # 10–20 s of HF model load on every regenerate.
        text = source
        if lang == "ks" and section == "executive_summary":
            cached_ks_text = report.ks_audio_text or (
                report.ks_translation.get("executive_summary")
                if isinstance(report.ks_translation, dict)
                else ""
            )
            if cached_ks_text:
                text = cached_ks_text
        if lang != "en" and text is source:
            unload_llm()
            try:
                text = get_translator().translate(
                    source, target_lang=lang, source_lang="en"
                )
            except Exception as exc:
                return Response(
                    {"detail": f"Translation step failed: {exc}"},
                    status=status.HTTP_502_BAD_GATEWAY,
                )

        # …then synthesise audio. Local Matcha runs at the configured
        # step count (1500 for the demo). The Modal client clamps to its
        # own ceiling (TTS_HTTP_MAX_STEPS=150) so passing 1500 there is
        # fine — it gets dialled down inside LocalHTTPTTS.
        try:
            result = get_tts(provider_override).synthesize(
                text, lang=lang, num_steps=settings.TTS_NUM_STEPS
            )
        except Exception as exc:
            return Response(
                {"detail": f"TTS step failed: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Persist the executive-summary narration so we don't synthesise it
        # again next time the user opens this session.
        if lang == "ks" and section == "executive_summary":
            report.ks_audio = bytes(result.audio)
            report.ks_audio_content_type = result.content_type or "audio/wav"
            report.ks_audio_text = text
            if report.localization_status != "completed":
                report.localization_status = "completed"
            report.save(
                update_fields=[
                    "ks_audio",
                    "ks_audio_content_type",
                    "ks_audio_text",
                    "localization_status",
                ]
            )

        response = HttpResponse(result.audio, content_type=result.content_type)
        response["Content-Disposition"] = (
            f'inline; filename="zeaniv-report-{lang}.wav"'
        )
        # Sanitised debug header — collapse whitespace so HTTP-1.1 won't reject it,
        # base64 the raw bytes for safety against non-Latin-1 chars.
        import base64

        response["X-Translated-Text"] = base64.b64encode(
            text[:1000].encode("utf-8")
        ).decode("ascii")
        return response
