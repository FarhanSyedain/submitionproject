"""Pick a TTS provider based on settings.TTS_PROVIDER."""
from __future__ import annotations

from django.conf import settings

from services.tts.base import BaseTTS


def get_tts(provider: str | None = None) -> BaseTTS:
    chosen = (provider or settings.TTS_PROVIDER or "local_http").lower()

    if chosen == "local_http":
        from services.tts.local_http_client import LocalHTTPTTS

        return LocalHTTPTTS(
            url=settings.TTS_URL,
            text_field=settings.TTS_TEXT_FIELD,
            lang_field=settings.TTS_LANG_FIELD,
            steps_field=settings.TTS_STEPS_FIELD,
            json_audio_field=settings.TTS_AUDIO_FIELD,
            auth_bearer=settings.TTS_AUTH_BEARER,
            max_steps=settings.TTS_HTTP_MAX_STEPS,
        )

    if chosen in ("local_matcha", "local"):
        from services.tts.local_matcha_client import LocalMatchaTTS

        return LocalMatchaTTS(
            ckpt_path=settings.TTS_LOCAL_CKPT_PATH,
            vocoder_path=settings.TTS_LOCAL_VOCODER_PATH,
            bolbosh_path=settings.TTS_LOCAL_BOLBOSH_PATH,
            device=settings.TTS_LOCAL_DEVICE,
            default_speaker_id=settings.TTS_LOCAL_SPEAKER_ID,
            default_speaking_rate=settings.TTS_LOCAL_SPEAKING_RATE,
            default_n_timesteps=settings.TTS_LOCAL_N_TIMESTEPS,
        )

    raise ValueError(f"Unknown TTS provider: {chosen}")
