"""실 ElevenLabs 호출로 ④/⑥ 검증 (Discord 없이).

  A) stream_mp3(HTTP, optimize_streaming_latency) 첫 MP3 청크 지연
  B) stream_ws(WebSocket overlap) — 증분 텍스트 피드 → 첫 오디오 지연
  C) stream_ws MP3 → ffmpeg(-f mp3 + nobuffer) → PCM s16le 48k 디코딩 확인

직접 실행: PYTHONPATH=. uv run python tests/verify_tts_live.py
"""
import asyncio
import os
import sys
import time

from dotenv import load_dotenv
import yaml

from core.tts import ElevenLabsTTS

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows cp949 콘솔에서 한글/기호 깨짐 방지
except Exception:
    pass

load_dotenv()
_cfg = yaml.safe_load(open("config.yaml", encoding="utf-8"))
tts = ElevenLabsTTS(
    api_key=os.environ["ELEVENLABS_API_KEY"],
    voice_id=os.environ["ELEVENLABS_VOICE_ID"],
    model=_cfg["tts"]["model"],
)


async def test_http():
    text = "안녕하세요. 오늘 일정은 오후 세 시 회의가 있어요."
    t0 = time.monotonic()
    first = None
    total = 0
    async for chunk in tts.stream_mp3(text):
        if first is None:
            first = time.monotonic() - t0
        total += len(chunk)
    print(f"A) HTTP stream_mp3: 첫 MP3 청크 {first:.2f}s, 총 {total}B")
    assert first is not None and total > 0
    return first


async def _text_feed():
    """LLM이 voice_response를 토큰 단위로 흘리는 상황 모사 (작은 지연 포함)."""
    parts = ["안녕하세요. ", "오늘 일정은 ", "오후 세 시 ", "회의가 있어요."]
    for p in parts:
        yield p
        await asyncio.sleep(0.15)  # 토큰 생성 간격 모사


async def test_ws():
    t0 = time.monotonic()
    first = None
    total = 0
    chunks = 0
    async for mp3 in tts.stream_ws(_text_feed()):
        if first is None:
            first = time.monotonic() - t0
        total += len(mp3)
        chunks += 1
    print(f"B) WS stream_ws: 첫 오디오 {first:.2f}s, {chunks}청크 총 {total}B")
    assert first is not None and total > 0
    return first


async def test_ws_ffmpeg():
    """WS MP3를 _play_mp3_stream과 동일한 ffmpeg 플래그로 PCM 디코딩되는지."""
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-f", "mp3", "-analyzeduration", "0", "-probesize", "32",
        "-fflags", "nobuffer", "-i", "pipe:0",
        "-f", "s16le", "-ar", "48000", "-ac", "2", "-loglevel", "quiet", "pipe:1",
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
    )
    pcm_total = 0

    async def feed():
        async for mp3 in tts.stream_ws(_text_feed()):
            proc.stdin.write(mp3)
        proc.stdin.close()

    async def read():
        nonlocal pcm_total
        while True:
            pcm = await proc.stdout.read(3840)
            if not pcm:
                break
            pcm_total += len(pcm)
        await proc.wait()

    await asyncio.gather(feed(), read())
    # 48k stereo s16le: 1초 = 192000B. 짧은 문장이라도 수만 바이트는 나와야 함
    print(f"C) WS->ffmpeg PCM: {pcm_total}B (~{pcm_total/192000:.2f}s 오디오)")
    assert pcm_total > 10000


async def _long_feed(delay=0.2):
    """50자 초과 긴 voice_response를 천천히 흘려 overlap을 실증."""
    parts = [
        "오늘은 ", "오전에 ", "캡스톤 ", "회의가 ", "있고 ", "오후 ", "세 시에는 ",
        "교수님 ", "면담이 ", "잡혀 ", "있어요. ", "저녁에는 ", "동아리 ", "모임이 ", "있습니다.",
    ]
    for p in parts:
        yield p
        await asyncio.sleep(delay)


async def test_ws_overlap():
    """긴 응답에서 첫 오디오가 전체 텍스트 피드 완료 *전에* 도착하면 overlap 성립."""
    feed_delay = 0.2
    t0 = time.monotonic()
    first = None
    async for mp3 in tts.stream_ws(_long_feed(feed_delay)):
        if first is None:
            first = time.monotonic() - t0
            break
    feed_total = 15 * feed_delay  # 전체 텍스트를 다 흘리는 데 걸리는 시간(~3.0s)
    overlapped = first < feed_total
    print(f"D) WS overlap(긴 응답): 첫 오디오 {first:.2f}s < 전체 피드 {feed_total:.2f}s ? {overlapped}")
    assert overlapped, "overlap 실패: 첫 오디오가 피드 완료 후 도착"
    return first


async def main():
    print("=== ElevenLabs 라이브 검증 ===")
    http_first = await test_http()
    ws_first = await test_ws()
    await test_ws_ffmpeg()
    overlap_first = await test_ws_overlap()
    print(f"\n첫음절 비교(짧은 응답): HTTP {http_first:.2f}s vs WS {ws_first:.2f}s")
    print(f"overlap 첫 오디오(긴 응답): {overlap_first:.2f}s — 생성이 피드 도중 시작됨")
    print("ALL LIVE TTS TESTS PASSED")


if __name__ == "__main__":
    asyncio.run(main())
