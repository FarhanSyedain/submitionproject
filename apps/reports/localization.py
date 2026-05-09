"""Post-pipeline Kashmiri localisation.

Runs once per session after the report agent finishes:
  1. Translate the report (executive summary, key insights, actions) into Kashmiri.
  2. Synthesise an audio narration of the executive summary using 150 diffusion
     steps for higher fidelity.
  3. Persist the translation and audio bytes onto the Report row so reopening
     a previous session is instant.

Designed to never raise — failures are recorded on `localization_status` /
`localization_error` and the calling pipeline keeps going.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Diffusion steps for the auto-generated narration come from
# settings.TTS_NUM_STEPS so the demo can crank quality (1500) without
# touching code, and we can drop back to 150 for fast iteration.


def generate_localization(report) -> str:
    """Translate + synthesise audio for `report`. Returns the final status."""
    from services.memory import unload_llm
    from services.translation import get_translator
    from services.tts import get_tts

    if not report.executive_summary:
        report.localization_status = "skipped"
        report.localization_error = "Report has no executive summary."
        report.save(
            update_fields=["localization_status", "localization_error"]
        )
        return "skipped"

    report.localization_status = "running"
    report.localization_error = ""
    report.save(update_fields=["localization_status", "localization_error"])

    # The HF translator and Ollama can both be heavy; free LLM memory first.
    unload_llm()

    actions = report.recommended_actions or []
    insights = report.key_insights or []

    sources = [
        report.executive_summary,
        *insights,
        *[a.get("action", "") for a in actions],
    ]

    try:
        translator = get_translator()
        translated = translator.translate_many(
            sources, target_lang="ks", source_lang="en"
        )
    except Exception as exc:
        logger.exception("Translation step failed for report %s", report.id)
        report.localization_status = "failed"
        report.localization_error = f"Translation failed: {exc}"
        report.save(
            update_fields=["localization_status", "localization_error"]
        )
        return "failed"

    idx = 0
    out_summary = translated[idx]
    idx += 1
    out_insights = []
    for original in insights:
        out_insights.append(translated[idx] if original else "")
        idx += 1
    out_actions = []
    for original in actions:
        translated_action = translated[idx] if original.get("action") else ""
        idx += 1
        out_actions.append({**original, "action": translated_action})

    report.ks_translation = {
        "lang": "ks",
        "language": "Kashmiri",
        "provider": getattr(translator, "provider", "unknown"),
        "executive_summary": out_summary,
        "key_insights": out_insights,
        "recommended_actions": out_actions,
    }
    report.ks_audio_text = out_summary
    report.save(update_fields=["ks_translation", "ks_audio_text"])

    try:
        from django.conf import settings

        tts = get_tts()
        result = tts.synthesize(
            out_summary, lang="ks", num_steps=settings.TTS_NUM_STEPS
        )
    except Exception as exc:
        logger.exception("TTS step failed for report %s", report.id)
        report.localization_status = "failed"
        report.localization_error = f"TTS failed: {exc}"
        report.save(
            update_fields=["localization_status", "localization_error"]
        )
        return "failed"

    report.ks_audio = bytes(result.audio)
    report.ks_audio_content_type = result.content_type or "audio/wav"
    report.localization_status = "completed"
    report.save(
        update_fields=[
            "ks_audio",
            "ks_audio_content_type",
            "localization_status",
        ]
    )
    return "completed"
