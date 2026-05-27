import asyncio
import logging

import numpy as np
from faster_whisper import WhisperModel

log = logging.getLogger(__name__)


class STTEngine:
    def __init__(
        self,
        model_size: str,
        device: str,
        compute_type: str,
        language: str,
        initial_prompt: str,
    ):
        log.info("Loading Whisper model: %s (device=%s, compute=%s)...", model_size, device, compute_type)
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self._language = language
        self._initial_prompt = initial_prompt
        log.info("STT engine ready")

    async def transcribe(self, pcm_int16: np.ndarray) -> str:
        """PCM int16 mono 16kHz → Korean transcript string."""
        audio = pcm_int16.astype(np.float32) / 32768.0
        loop = asyncio.get_event_loop()
        def _run():
            segs, _ = self._model.transcribe(
                audio,
                language=self._language,
                initial_prompt=self._initial_prompt,
                beam_size=5,
                vad_filter=True,
            )
            return "".join(seg.text for seg in segs).strip()  # generator를 executor 안에서 소비

        return await loop.run_in_executor(None, _run)
