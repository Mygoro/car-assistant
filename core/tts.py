"""Phase 5: ElevenLabs TTS 클라이언트 + Discord 음성 송출."""
import asyncio
import base64
import io
import json
import logging
import math
import queue
import struct
import time
from pathlib import Path

import discord
import httpx
import websockets

log = logging.getLogger(__name__)


class ElevenLabsTTS:
    BASE_URL = "https://api.elevenlabs.io/v1"

    def __init__(self, api_key: str, voice_id: str, model: str):
        self.api_key = api_key
        self.voice_id = voice_id
        self.model = model

    async def stream_mp3(self, text: str):
        """text → MP3 bytes 스트리밍 (async generator)."""
        # optimize_streaming_latency: 첫 바이트 지연 최소화 (3 = 공격적, 약간의 정규화 생략)
        url = (
            f"{self.BASE_URL}/text-to-speech/{self.voice_id}/stream"
            "?optimize_streaming_latency=3"
        )
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

    async def stream_ws(self, text_aiter):
        """텍스트 청크(AsyncIterator[str])를 ElevenLabs WS로 흘려보내며 MP3 bytes를 yield.

        LLM이 voice_response를 생성하는 *동안* 부분 텍스트를 밀어넣어 TTS 생성을
        LLM과 겹친다(overlap). HTTP stream_mp3가 전체 텍스트를 받아야 시작하는 것과 달리,
        WS는 텍스트가 도착하는 족족 합성을 시작한다.
        """
        ws_url = (
            f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input"
            f"?model_id={self.model}&optimize_streaming_latency=3"
        )
        async with websockets.connect(
            ws_url, additional_headers={"xi-api-key": self.api_key}
        ) as ws:
            # BOS: 보이스 설정 + 낮은 chunk_length_schedule로 첫 합성을 앞당김(최소 50자)
            await ws.send(json.dumps({
                "text": " ",
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                "generation_config": {"chunk_length_schedule": [50]},
            }))

            async def _send():
                async for chunk in text_aiter:
                    if chunk:
                        await ws.send(json.dumps({"text": chunk}))
                await ws.send(json.dumps({"text": ""}))  # EOS

            send_task = asyncio.create_task(_send())
            try:
                async for message in ws:
                    data = json.loads(message)
                    audio = data.get("audio")
                    if audio:
                        yield base64.b64decode(audio)
                    if data.get("isFinal"):
                        break
            finally:
                if not send_task.done():
                    send_task.cancel()
                try:
                    await send_task
                except (asyncio.CancelledError, Exception):
                    pass


class _StreamingPCMAudio(discord.AudioSource):
    """ElevenLabs MP3 → ffmpeg PCM → Discord를 버퍼링 없이 실시간 연결하는 AudioSource.

    async 쪽(PCM 생산자)에서 push()/finish()로 데이터를 밀어 넣고,
    Discord 오디오 스레드(소비자)에서 read()로 20ms 단위로 꺼낸다.
    queue.Queue가 두 스레드를 브릿지한다.
    """
    FRAME = 3840  # 20ms @ 48kHz stereo s16le

    def __init__(self) -> None:
        self._q: queue.Queue[bytes | None] = queue.Queue(maxsize=200)
        self._buf = b""

    # ── 생산자 (async 컨텍스트) ──────────────────────────────────────

    def push(self, data: bytes) -> None:
        self._buf += data
        while len(self._buf) >= self.FRAME:
            self._q.put(self._buf[: self.FRAME])
            self._buf = self._buf[self.FRAME :]

    def finish(self) -> None:
        if self._buf:
            self._q.put(self._buf + bytes(self.FRAME - len(self._buf)))
        self._q.put(None)  # sentinel

    # ── 소비자 (Discord 오디오 스레드) ──────────────────────────────

    def read(self) -> bytes:
        try:
            chunk = self._q.get(timeout=0.5)
        except queue.Empty:
            return bytes(self.FRAME)  # 버퍼 언더런 → 무음
        return chunk if chunk is not None else b""

    def is_opus(self) -> bool:
        return False

    def cleanup(self) -> None:
        pass


async def _play_mp3_stream(
    voice_client: discord.VoiceClient,
    mp3_aiter,
    wake_detector=None,
) -> None:
    """MP3 bytes 스트림(async gen)을 ffmpeg→PCM→Discord로 즉시 재생하는 공용 경로.

    첫 PCM 청크가 나오는 순간 재생을 시작해 체감 지연을 줄인다.
    stream_mp3(HTTP)와 stream_ws(WebSocket) 둘 다 이 헬퍼를 공유한다.
    """
    try:
        ffmpeg_proc = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-f", "mp3",              # 입력이 MP3임을 명시 → 포맷 탐지 probe 생략(지연↓)
            "-analyzeduration", "0",  # 입력 분석 대기 제거
            "-probesize", "32",
            "-fflags", "nobuffer",
            "-i", "pipe:0",
            "-f", "s16le", "-ar", "48000", "-ac", "2",
            "-loglevel", "quiet",
            "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        log.error("ffmpeg not found — TTS 송출 불가")
        return

    source = _StreamingPCMAudio()

    async def _feed() -> None:
        try:
            async for chunk in mp3_aiter:
                ffmpeg_proc.stdin.write(chunk)
        except Exception:
            log.exception("ElevenLabs 스트리밍 오류")
        finally:
            ffmpeg_proc.stdin.close()

    async def _read_pcm() -> None:
        while True:
            pcm = await ffmpeg_proc.stdout.read(_StreamingPCMAudio.FRAME)
            if not pcm:
                break
            source.push(pcm)
        source.finish()
        await ffmpeg_proc.wait()

    feed_task = asyncio.create_task(_feed())
    pcm_task = asyncio.create_task(_read_pcm())

    # 첫 PCM 청크가 큐에 쌓일 때까지 대기 → 재생 시작
    t_speak_start = time.monotonic()
    while source._q.empty() and not pcm_task.done():
        await asyncio.sleep(0.01)
    log.info("[TIMING] 🔊 TTS 첫음절: %.2fs", time.monotonic() - t_speak_start)

    if wake_detector is not None:
        wake_detector.pause()
    try:
        voice_client.play(source)
        # PCM 생산 완료 + Discord 재생 완료까지 대기
        await pcm_task
        await feed_task
        while voice_client.is_playing():
            await asyncio.sleep(0.05)
    finally:
        if wake_detector is not None:
            wake_detector.resume()


async def speak(
    voice_client: discord.VoiceClient,
    tts: ElevenLabsTTS,
    text: str,
    wake_detector=None,
) -> None:
    """완성된 voice_response 문자열을 HTTP 스트리밍 TTS로 재생(폴백/단발 경로)."""
    if not text.strip():
        return
    await _play_mp3_stream(voice_client, tts.stream_mp3(text), wake_detector)


async def speak_streaming(
    voice_client: discord.VoiceClient,
    tts: ElevenLabsTTS,
    text_aiter,
    wake_detector=None,
) -> None:
    """voice_response 토큰 스트림을 WebSocket TTS로 LLM과 겹쳐 재생(⑥ overlap 경로)."""
    await _play_mp3_stream(voice_client, tts.stream_ws(text_aiter), wake_detector)


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
