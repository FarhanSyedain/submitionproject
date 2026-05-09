"""In-process Kashmiri TTS using a Bolbosh / Matcha-TTS checkpoint.

Mirrors `modal_app/app.py` from the klm/Bolbosh repo, but loads the model
inside the Django process — no Modal, no HTTP hop, no auth token. Useful
when you have the checkpoint on disk and want to run TTS offline.

Requirements (pip):
  * torch              — already in requirements.txt
  * soundfile          — for WAV encoding
  * Bolbosh fork of matcha-tts (NOT the pypi `matcha-tts`, which has the
    wrong vocab and would garble Kashmiri). Either `pip install -e
    /path/to/Bolbosh`, or set TTS_LOCAL_BOLBOSH_PATH and we'll prepend it
    to sys.path at load time.
  * KashmiriNormalizer — `pip install
    git+https://github.com/abdulmuizz0903/KashmiriNormalizer`

The model + vocoder are loaded lazily on first synth (~5–30 s on CPU,
~1–3 s on GPU) and reused for the rest of the process lifetime.
"""
from __future__ import annotations

import io
import logging
import os
import sys
import threading
import urllib.request
from pathlib import Path

from services.tts.base import BaseTTS, TTSResult

logger = logging.getLogger(__name__)

DEFAULT_VOCODER_URL = (
    "https://github.com/shivammehta25/Matcha-TTS-checkpoints/"
    "releases/download/v1.0/g_02500000"
)


class LocalMatchaTTS(BaseTTS):
    """Loads `model.ckpt` directly and runs inference in-process."""

    provider = "local_matcha"

    def __init__(
        self,
        ckpt_path: str,
        *,
        vocoder_path: str = "",
        vocoder_url: str = DEFAULT_VOCODER_URL,
        bolbosh_path: str = "",
        device: str = "auto",
        default_speaker_id: int = 423,
        default_speaking_rate: float = 1.0,
        default_n_timesteps: int = 20,
        denoiser_strength: float = 0.00025,
        temperature: float = 0.667,
        sample_rate: int = 22050,
    ) -> None:
        if not ckpt_path:
            raise ValueError("TTS_LOCAL_CKPT_PATH is required for LocalMatchaTTS")
        if not Path(ckpt_path).exists():
            raise FileNotFoundError(f"TTS checkpoint not found: {ckpt_path}")

        self.ckpt_path = str(Path(ckpt_path).resolve())
        # Default the vocoder cache to sit next to the checkpoint so we
        # don't clobber the user's home with random binary blobs.
        self.vocoder_path = str(
            Path(vocoder_path).resolve()
            if vocoder_path
            else Path(self.ckpt_path).parent / "hifigan_univ_v1"
        )
        self.vocoder_url = vocoder_url
        self.bolbosh_path = str(Path(bolbosh_path).resolve()) if bolbosh_path else ""
        self.device_pref = device
        self.default_speaker_id = int(default_speaker_id)
        self.default_speaking_rate = float(default_speaking_rate)
        self.default_n_timesteps = int(default_n_timesteps)
        self.denoiser_strength = float(denoiser_strength)
        self.temperature = float(temperature)
        self.sample_rate = int(sample_rate)

        self._lock = threading.Lock()
        self._loaded = False
        self._model = None
        self._hifigan = None
        self._denoiser = None
        self._device = None
        self._text_to_sequence = None
        self._intersperse = None

    def _resolve_device(self):
        import torch

        pref = (self.device_pref or "auto").lower()
        if pref == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
                return torch.device("mps")
            return torch.device("cpu")
        return torch.device(pref)

    def _ensure_bolbosh_on_path(self) -> None:
        if self.bolbosh_path and self.bolbosh_path not in sys.path:
            sys.path.insert(0, self.bolbosh_path)

    def _ensure_vocoder(self) -> None:
        path = Path(self.vocoder_path)
        if path.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("[tts] downloading HiFi-GAN vocoder to %s", path)
        urllib.request.urlretrieve(self.vocoder_url, str(path))

    def _load(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return

            self._ensure_bolbosh_on_path()

            # The Bolbosh checkpoint was saved with non-tensor metadata, so
            # the post-2.4 weights-only default rejects it. Match how the
            # Modal app loads it.
            os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "1")

            import torch

            from matcha.hifigan.config import v1
            from matcha.hifigan.denoiser import Denoiser
            from matcha.hifigan.env import AttrDict
            from matcha.hifigan.models import Generator as HiFiGAN
            from matcha.models.matcha_tts import MatchaTTS
            from matcha.text import text_to_sequence
            from matcha.utils.utils import intersperse

            self._device = self._resolve_device()
            logger.info(
                "[tts] loading Bolbosh checkpoint from %s on %s",
                self.ckpt_path, self._device,
            )
            self._model = MatchaTTS.load_from_checkpoint(
                self.ckpt_path, map_location=self._device
            )
            self._model.eval()

            self._ensure_vocoder()
            h = AttrDict(v1)
            self._hifigan = HiFiGAN(h).to(self._device)
            ck = torch.load(self.vocoder_path, map_location=self._device)
            self._hifigan.load_state_dict(ck["generator"])
            self._hifigan.eval()
            self._hifigan.remove_weight_norm()

            self._denoiser = Denoiser(self._hifigan, mode="zeros")
            self._text_to_sequence = text_to_sequence
            self._intersperse = intersperse
            self._loaded = True
            logger.info("[tts] local Matcha-TTS ready on %s", self._device)

    def synthesize(
        self,
        text: str,
        *,
        lang: str = "ks",  # noqa: ARG002 — accepted for interface parity
        num_steps: int | None = None,
        speaker_id: int | None = None,
        speaking_rate: float | None = None,
    ) -> TTSResult:
        if not text or not text.strip():
            raise ValueError("Cannot synthesize empty text")

        self._load()

        import time as _time

        import soundfile as sf
        import torch

        n_timesteps = int(
            num_steps if num_steps is not None else self.default_n_timesteps
        )
        spk_id = int(
            speaker_id if speaker_id is not None else self.default_speaker_id
        )
        rate = float(
            speaking_rate
            if speaking_rate is not None
            else self.default_speaking_rate
        )

        logger.info(
            "[matcha] synth start — chars=%d steps=%d spk=%d rate=%.2f device=%s",
            len(text), n_timesteps, spk_id, rate, self._device,
        )
        t_start = _time.monotonic()

        seq, _ = self._text_to_sequence(text, ["basic_cleaners"])
        x = torch.tensor(
            self._intersperse(seq, 0),
            dtype=torch.long,
            device=self._device,
        )[None]
        x_lengths = torch.tensor(
            [x.shape[-1]], dtype=torch.long, device=self._device
        )
        spk = torch.tensor([spk_id], dtype=torch.long, device=self._device)

        with torch.inference_mode():
            output = self._model.synthesise(
                x, x_lengths,
                n_timesteps=n_timesteps,
                temperature=self.temperature,
                spks=spk,
                length_scale=rate,
            )
            wav = self._hifigan(output["mel"]).clamp(-1, 1)
            wav = (
                self._denoiser(wav.squeeze(), strength=self.denoiser_strength)
                .cpu()
                .squeeze()
            )

        buf = io.BytesIO()
        sf.write(
            buf, wav.numpy(), samplerate=self.sample_rate,
            format="WAV", subtype="PCM_16",
        )
        audio_bytes = buf.getvalue()
        logger.info(
            "[matcha] synth done  — %.2fs, %d bytes (%.1fs audio @ %d Hz)",
            _time.monotonic() - t_start,
            len(audio_bytes),
            wav.numel() / self.sample_rate,
            self.sample_rate,
        )
        return TTSResult(
            audio=audio_bytes,
            content_type="audio/wav",
            sample_rate=self.sample_rate,
        )
