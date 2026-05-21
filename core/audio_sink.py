import asyncio
import audioop
import os
import time
import wave
from pathlib import Path

import numpy as np
from discord.ext.voice_recv import AudioSink
from discord.ext.voice_recv.opus import VoiceData

DEBUG_DIR = Path("archive/audio/debug")


class CarAudioSink(AudioSink):
    """Receives audio from OWNER_USER_ID, downsamples to 16kHz mono, pushes to queue."""

    def __init__(self, loop: asyncio.AbstractEventLoop, pcm_queue: asyncio.Queue):
        super().__init__()
        self._loop = loop
        self._pcm_queue = pcm_queue
        self._owner_id = int(os.environ["DISCORD_OWNER_USER_ID"])
        self._ratecv_state = None

        # Debug WAV accumulation (Phase 1 only)
        self._debug_buf: list[bytes] = []
        self._last_save = time.monotonic()

    def wants_opus(self) -> bool:
        return False  # request decoded PCM from the library

    def write(self, user, data: VoiceData) -> None:
        if user is None or user.id != self._owner_id:
            return

        pcm_48k_stereo: bytes = data.pcm
        n = len(pcm_48k_stereo)
        print(f"AUDIO_RECEIVED: {n} bytes")

        # Stereo → mono: average left and right channels
        samples = np.frombuffer(pcm_48k_stereo, dtype=np.int16)
        mono = samples.reshape(-1, 2).mean(axis=1).astype(np.int16)
        mono_bytes = mono.tobytes()

        # 48kHz → 16kHz
        pcm_16k, self._ratecv_state = audioop.ratecv(
            mono_bytes, 2, 1, 48000, 16000, self._ratecv_state
        )

        chunk = np.frombuffer(pcm_16k, dtype=np.int16)
        self._loop.call_soon_threadsafe(self._pcm_queue.put_nowait, chunk)

        self._debug_buf.append(pcm_16k)
        if time.monotonic() - self._last_save >= 5.0:
            asyncio.run_coroutine_threadsafe(self._flush_debug_wav(), self._loop)
            self._last_save = time.monotonic()

    async def _flush_debug_wav(self):
        if not self._debug_buf:
            return
        buf = b"".join(self._debug_buf)
        self._debug_buf = []
        DEBUG_DIR.mkdir(parents=True, exist_ok=True)
        path = DEBUG_DIR / f"debug_audio_{int(time.time())}.wav"
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(buf)
        print(f"DEBUG_WAV saved: {path}")

    def cleanup(self):
        pass
