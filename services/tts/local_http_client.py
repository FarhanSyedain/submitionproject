"""Generic HTTP TTS client. Point it at any local TTS service.

Default contract (override via .env):

    POST {TTS_URL}
    Content-Type: application/json
    Body: {"text": "...", "lang": "ks"}

The response can be either:
  * Raw audio bytes (Content-Type: audio/wav | audio/mpeg | audio/ogg…)
  * JSON {"audio": "<base64>"} where the key is configurable

The client auto-detects which based on Content-Type.
"""
from __future__ import annotations

import base64
import logging

import requests

from services.tts.base import BaseTTS, TTSResult

logger = logging.getLogger(__name__)


class LocalHTTPTTS(BaseTTS):
    provider = "local_http"

    def __init__(
        self,
        url: str,
        *,
        timeout: int = 600,
        text_field: str = "text",
        lang_field: str = "lang",  # set to "" to omit lang from the payload
        steps_field: str = "n_timesteps",  # set to "" to omit
        json_audio_field: str = "audio",
        json_content_type: str = "audio/wav",
        auth_bearer: str = "",
        extra_payload: dict | None = None,
        max_steps: int | None = None,
    ) -> None:
        if not url:
            raise ValueError("TTS_URL is required for LocalHTTPTTS")
        self.url = url
        self.timeout = timeout
        self.text_field = text_field
        self.lang_field = lang_field
        self.steps_field = steps_field
        self.json_audio_field = json_audio_field
        self.json_content_type = json_content_type
        self.auth_bearer = auth_bearer
        self.extra_payload = extra_payload or {}
        # Hard ceiling on diffusion steps. The Modal endpoint validates
        # `n_timesteps <= 500` and gets very slow above ~150, so we clamp
        # here regardless of what the caller asks for.
        self.max_steps = max_steps

    def synthesize(
        self,
        text: str,
        *,
        lang: str = "ks",
        num_steps: int | None = None,
    ) -> TTSResult:
        if not text.strip():
            raise ValueError("Cannot synthesize empty text")

        payload: dict = {self.text_field: text, **self.extra_payload}
        if self.lang_field:  # skip if the server doesn't take a lang field
            payload[self.lang_field] = lang
        if num_steps is not None and self.steps_field:
            steps = int(num_steps)
            if self.max_steps is not None and steps > self.max_steps:
                steps = self.max_steps
            payload[self.steps_field] = steps

        headers = {}
        if self.auth_bearer:
            headers["Authorization"] = f"Bearer {self.auth_bearer}"

        # Use a fresh `requests.Session` per call (and close it) so we
        # never reuse a TLS connection from urllib3's pool. This avoids
        # the intermittent `SSLV3_ALERT_BAD_RECORD_MAC` alert that fires
        # when a stale keep-alive socket lands in the wrong worker. Also
        # send `Connection: close` so the server tears the socket down on
        # its side. Retry a few times on SSL / connection errors before
        # giving up — these alerts can string together for 1–3 attempts.
        import time as _time

        request_headers = {**headers, "Connection": "close"}
        steps_log = payload.get(self.steps_field) if self.steps_field else None
        logger.info(
            "[modal] POST %s — chars=%d steps=%s",
            self.url, len(text), steps_log,
        )
        t_start = _time.monotonic()

        last_exc: Exception | None = None
        response = None
        for attempt in range(4):
            session = requests.Session()
            try:
                response = session.post(
                    self.url,
                    json=payload,
                    headers=request_headers,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                last_exc = None
                logger.info(
                    "[modal] response 200 — attempt=%d, %.2fs, %d bytes",
                    attempt + 1,
                    _time.monotonic() - t_start,
                    len(response.content),
                )
                break
            except (
                requests.exceptions.SSLError,
                requests.exceptions.ConnectionError,
            ) as exc:
                last_exc = exc
                logger.warning(
                    "[modal] transport error attempt=%d after %.2fs — %s: %s",
                    attempt + 1,
                    _time.monotonic() - t_start,
                    type(exc).__name__,
                    str(exc)[:200],
                )
                _time.sleep(0.4 * (attempt + 1))
                continue
            finally:
                session.close()
        if last_exc is not None or response is None:
            logger.error(
                "[modal] giving up after %.2fs — %s",
                _time.monotonic() - t_start, last_exc,
            )
            raise last_exc if last_exc else RuntimeError("TTS request failed")

        content_type = (response.headers.get("Content-Type") or "").lower()

        # Raw audio response.
        if content_type.startswith("audio/"):
            return TTSResult(audio=response.content, content_type=content_type)

        # JSON-wrapped base64 audio.
        if "application/json" in content_type:
            data = response.json()
            blob = data
            for part in self.json_audio_field.split("."):
                if not isinstance(blob, dict):
                    break
                blob = blob.get(part, "")
            if not blob:
                raise RuntimeError(
                    f"TTS response missing '{self.json_audio_field}': {data!r}"
                )
            audio_bytes = base64.b64decode(blob)
            return TTSResult(audio=audio_bytes, content_type=self.json_content_type)

        # Unknown — assume raw audio.
        return TTSResult(audio=response.content, content_type="audio/wav")
