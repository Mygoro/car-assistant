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

    # 알려진 Whisper 한국어 hallucination 패턴 — 무음/배경소음에서 자주 발생
    _HALLUCINATIONS = {
        "자막 제공 및 광고를 포함하고 있습니다",
        "자막 제공 및 영상 제공 및 광고를 포함하고 있습니다",
        "한글자막",
        "한글 자막",
        "구독과 좋아요 부탁드립니다",
        "구독과 좋아요",
        "시청해 주셔서 감사합니다",
        "MBC 뉴스입니다",
        "KBS 뉴스입니다",
    }

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
                no_speech_threshold=0.6,       # 이 값 초과하는 세그먼트 자동 폐기
                condition_on_previous_text=False,  # 이전 컨텍스트 hallucination 전파 방지
            )
            # generator를 executor 안에서 소비, 세그먼트별 no_speech_prob 필터
            parts: list[str] = []
            for seg in segs:
                if seg.no_speech_prob > 0.6:
                    log.debug("Segment dropped (no_speech_prob=%.2f): %s", seg.no_speech_prob, seg.text.strip())
                    continue
                parts.append(seg.text)
            text = "".join(parts).strip()

            # 남은 known hallucination 블랙리스트 필터
            for pattern in self._HALLUCINATIONS:
                if pattern in text:
                    log.warning("Hallucination filtered: %s", text)
                    text = text.replace(pattern, "").strip().rstrip(".")
            return text

        return await loop.run_in_executor(None, _run)
