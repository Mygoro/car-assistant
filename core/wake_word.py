import asyncio
import logging
from pathlib import Path

import numpy as np
from openwakeword.model import Model

log = logging.getLogger(__name__)

_CHUNK = 1280        # 80ms at 16kHz
# 연속 N프레임이 threshold를 넘어야 감지 확정 — 단발 노이즈/오탐 차단
_CONFIRM_FRAMES = 1  # 단발 고신뢰 감지


class WakeWordDetector:
    def __init__(self, model_path: str = "wake_word/crank_otto.onnx", threshold: float = 0.5):
        self._threshold = threshold
        self._paused = False
        self._pcm_buf = np.array([], dtype=np.int16)
        self._streak = 0

        model_file = Path(model_path)
        if not model_file.exists():
            raise FileNotFoundError(
                f"Wake word model not found: {model_path}\n"
                "Run: uv run tools/train_wake_word.py"
            )

        log.info("Loading wake word model: %s (threshold=%.2f)", model_path, threshold)
        self._model = Model(wakeword_models=[str(model_file)], inference_framework="onnx")
        self._model_name = model_file.stem  # "crank_otto"
        log.info("Wake word gate ready")

    def pause(self):
        self._paused = True

    def resume(self):
        self._paused = False
        self._pcm_buf = np.array([], dtype=np.int16)
        self._streak = 0
        self._model.reset()

    async def process(self, pcm_chunk: np.ndarray) -> bool:
        """PCM int16 청크를 받아 wake word 감지 시 True 반환."""
        if self._paused:
            return False

        self._pcm_buf = np.concatenate([self._pcm_buf, pcm_chunk])

        while len(self._pcm_buf) >= _CHUNK:
            frame = self._pcm_buf[:_CHUNK]
            self._pcm_buf = self._pcm_buf[_CHUNK:]

            prediction = await asyncio.get_event_loop().run_in_executor(
                None, self._model.predict, frame
            )
            score = float(prediction.get(self._model_name, 0.0))
            if score > 0.1:
                log.debug("Wake word score: %.3f streak=%d", score, self._streak)
            if score >= self._threshold:
                self._streak += 1
                if self._streak >= _CONFIRM_FRAMES:
                    log.info("Wake word detected! score=%.3f streak=%d", score, self._streak)
                    self._model.reset()
                    self._pcm_buf = np.array([], dtype=np.int16)
                    self._streak = 0
                    return True
            else:
                self._streak = 0

        return False
