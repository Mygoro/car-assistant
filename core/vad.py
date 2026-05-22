import audioop
import logging
import urllib.request
from pathlib import Path

import numpy as np
import onnxruntime as ort

log = logging.getLogger(__name__)

_VAD_CHUNK = 512   # 32ms at 16kHz
_SILERO_URL = (
    "https://github.com/snakers4/silero-vad/raw/master"
    "/src/silero_vad/data/silero_vad.onnx"
)


class SileroVAD:
    """Silero VAD via ONNX Runtime (no PyTorch dependency)."""

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold
        path = Path("silero_vad.onnx")
        if not path.exists():
            log.info("Downloading Silero VAD model...")
            urllib.request.urlretrieve(_SILERO_URL, path)
        self._sess = ort.InferenceSession(str(path))
        input_names = {inp.name for inp in self._sess.get_inputs()}
        if "state" in input_names:
            self._api = "v4"
            self._state = np.zeros((2, 1, 128), dtype=np.float32)
        else:
            self._api = "v2"
            self._h = np.zeros((2, 1, 64), dtype=np.float32)
            self._c = np.zeros((2, 1, 64), dtype=np.float32)
        self._sr8k = np.array(8000, dtype=np.int64)
        self._ratecv_state = None  # audioop.ratecv 상태
        log.info("SileroVAD ready (api=%s, threshold=%.2f)", self._api, threshold)

    def is_speech(self, pcm_chunk: np.ndarray) -> bool:
        """pcm_chunk: 512 samples int16 at 16kHz. 내부적으로 8kHz로 다운샘플링."""
        # 이 ONNX 모델은 8kHz 입력에서만 정상 작동함
        pcm8k, self._ratecv_state = audioop.ratecv(
            pcm_chunk.tobytes(), 2, 1, 16000, 8000, self._ratecv_state
        )
        audio = np.frombuffer(pcm8k, dtype=np.int16).astype(np.float32) / 32768.0
        audio = audio[np.newaxis, :]
        if self._api == "v4":
            out, self._state = self._sess.run(
                None,
                {"input": audio, "sr": self._sr8k, "state": self._state},
            )
        else:
            out, self._h, self._c = self._sess.run(
                None,
                {"input": audio, "sr": self._sr8k, "h": self._h, "c": self._c},
            )
        return float(out[0][0]) > self.threshold

    def reset(self):
        if self._api == "v4":
            self._state[:] = 0
        else:
            self._h[:] = 0
            self._c[:] = 0
        self._ratecv_state = None
