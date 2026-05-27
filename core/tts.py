"""Phase 5: ElevenLabs TTS 클라이언트 + Discord 음성 송출."""
import asyncio
import io
import logging
import math
import struct
from pathlib import Path

import discord
import httpx

log = logging.getLogger(__name__)


class ElevenLabsTTS:
    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str, voice_id: str, model: str):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model

    async def stream_mp3(self, text: str):
        """text → MP3 bytes 스트리밍 (async generator)."""
        url = f"{self.BASE_URL}/text-to-speech/{self.voice_id}/stream"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        body = {
            "text": text,
            "model_id": self.model,
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, headers=headers, json=body) as resp:
                resp.raise_for_status()
                async for chunk in resp.aiter_bytes(chunk_size=1024):
                    yield chunk


async def speak(
    voice_client: discord.VoiceClient,
    tts: ElevenLabsTTS,
    text: str,
    wake_detector=None,
) -> None:
    """voice_response 텍스트를 TTS 변환 후 Discord 음성 채널로 송출.

    wake_detector가 전달되면 재생 중 wake word 감지를 일시 정지한다.
    """
    if not text.strip():
        return

    # MP3 → ffmpeg → PCM 48kHz stereo
    try:
        ffmpeg_proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-i", "pipe:0",
            "-f", "s16le", "-ar", "48000", "-ac", "2",
            "-loglevel", "quiet",
            "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        log.error("ffmpeg not found — TTS 송출 불가")
        return

    async def _feed():
        try:
            async for chunk in tts.stream_mp3(text):
                ffmpeg_proc.stdin.write(chunk)
        except Exception:
            log.exception("ElevenLabs 스트리밍 오류")
        finally:
            ffmpeg_proc.stdin.close()

    feed_task = asyncio.create_task(_feed())

    pcm_parts: list[bytes] = []
    while True:
        chunk = await ffmpeg_proc.stdout.read(3840)  # 40ms @ 48kHz stereo s16le
        if not chunk:
            break
        pcm_parts.append(chunk)

    await feed_task
    await ffmpeg_proc.wait()

    pcm_data = b"".join(pcm_parts)
    if not pcm_data:
        log.warning("ffmpeg PCM 출력 없음 — TTS 송출 skip")
        return

    if wake_detector is not None:
        wake_detector.pause()
    try:
        source = discord.PCMAudio(io.BytesIO(pcm_data))
        voice_client.play(source)
        while voice_client.is_playing():
            await asyncio.sleep(0.05)
    finally:
        if wake_detector is not None:
            wake_detector.resume()


async def play_cue(voice_client: discord.VoiceClient, path: str | Path) -> None:
    """효과음 MP3 파일을 Discord 음성 채널로 송출. 파일 없으면 조용히 skip."""
    p = Path(path)
    if not p.exists():
        log.warning("Cue file not found: %s", p)
        return
    # 이전 재생이 끝날 때까지 대기 (Already playing audio 예외 방지)
    wait_deadline = asyncio.get_event_loop().time() + 3.0
    while voice_client.is_playing() and asyncio.get_event_loop().time() < wait_deadline:
        await asyncio.sleep(0.02)
    if voice_client.is_playing():
        log.warning("play_cue: previous audio still playing after 3s — skipping %s", p.name)
        return
    log.info("CUE ▶ %s", p.name)
    source = discord.FFmpegPCMAudio(str(p))
    try:
        voice_client.play(source)
    except Exception:
        log.exception("play_cue: voice_client.play() failed for %s", p.name)
        return
    deadline = asyncio.get_event_loop().time() + 5.0
    while voice_client.is_playing() and asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(0.02)
    log.info("CUE ■ %s", p.name)


async def play_tone(voice_client: discord.VoiceClient, freq: int, duration: float = 0.12) -> None:
    """짧은 비프음을 Discord 음성 채널로 송출 (클릭 방지 fade in/out 포함)."""
    sample_rate = 48000
    n = int(sample_rate * duration)
    fade_samples = int(sample_rate * 0.01)  # 10ms fade
    pcm = bytearray()
    for i in range(n):
        t = i / sample_rate
        fade = min(i / fade_samples, 1.0, (n - i) / fade_samples)
        val = int(math.sin(2 * math.pi * freq * t) * fade * 0.35 * 32767)
        sample = struct.pack("<h", max(-32767, min(32767, val)))
        pcm += sample + sample  # stereo
    source = discord.PCMAudio(io.BytesIO(bytes(pcm)))
    voice_client.play(source)
    while voice_client.is_playing():
        await asyncio.sleep(0.02)


async def speak_local(tts: ElevenLabsTTS, text: str) -> None:
    """voice_response를 로컬 스피커로 재생 (마이크 없는 개발/테스트용)."""
    import numpy as np
    try:
        import sounddevice as sd
    except ImportError:
        log.error("sounddevice 미설치 — uv add sounddevice")
        return

    if not text.strip():
        return

    try:
        ffmpeg_proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-i", "pipe:0",
            "-f", "s16le", "-ar", "44100", "-ac", "2",
            "-loglevel", "quiet",
            "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        log.error("ffmpeg not found — speak_local 불가")
        return

    async def _feed():
        try:
            async for chunk in tts.stream_mp3(text):
                ffmpeg_proc.stdin.write(chunk)
        except Exception:
            log.exception("ElevenLabs 스트리밍 오류")
        finally:
            ffmpeg_proc.stdin.close()

    feed_task = asyncio.create_task(_feed())

    pcm_parts: list[bytes] = []
    while True:
        chunk = await ffmpeg_proc.stdout.read(4096)
        if not chunk:
            break
        pcm_parts.append(chunk)

    await feed_task
    await ffmpeg_proc.wait()

    pcm_data = b"".join(pcm_parts)
    if not pcm_data:
        log.warning("PCM 출력 없음 — speak_local skip")
        return

    audio = np.frombuffer(pcm_data, dtype=np.int16).reshape(-1, 2)
    sd.play(audio, samplerate=44100)
    await asyncio.get_event_loop().run_in_executor(None, sd.wait)


async def play_filler(voice_client: discord.VoiceClient, filler_key: str = "default") -> None:
    """사전 녹음된 필러 MP3를 Discord 음성 채널로 송출.

    파일이 없으면 조용히 skip한다.
    """
    filler_map = {
        "searching": "fillers/chatgo_itda.mp3",
        "confirming": "fillers/hwagin_jung.mp3",
        "default":    "fillers/jamsiman.mp3",
    }
    path = Path(filler_map.get(filler_key, filler_map["default"]))
    if not path.exists():
        log.debug("Filler file not found: %s — skip", path)
        return

    source = discord.FFmpegPCMAudio(str(path))
    voice_client.play(source)
    while voice_client.is_playing():
        await asyncio.sleep(0.05)
