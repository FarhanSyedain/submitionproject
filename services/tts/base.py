"""Abstract TTS interface."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TTSResult:
    audio: bytes
    content_type: str = "audio/wav"
    sample_rate: int | None = None


class BaseTTS:
    provider: str = "base"

    def synthesize(
        self,
        text: str,
        *,
        lang: str = "ks",
        num_steps: int | None = None,
    ) -> TTSResult:
        raise NotImplementedError
