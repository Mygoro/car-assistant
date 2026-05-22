#!/usr/bin/env python
"""
ElevenLabs 여러 목소리로 "크랭크 오토" TTS 샘플 생성.
화자 독립 모델 학습을 위한 다화자 positive 데이터를 만든다.

사용법:
  uv run tools/generate_tts_samples.py

출력:
  wake_word/training_data/positive/tts_<voice>_<n>.wav
"""

import asyncio
import audioop
import io
import wave
from pathlib import Path

import httpx
import numpy as np
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.environ["ELEVENLABS_API_KEY"]
BASE_URL = "https://api.elevenlabs.io/v1"
OUTPUT_DIR = Path("wake_word/training_data/positive")
SR_TARGET = 16000

# ElevenLabs 기본 제공 목소리 (무료 플랜 사용 가능)
# 다양한 성별·억양으로 구성
VOICES = {
    "rachel":   "21m00Tcm4TlvDq8ikWAM",  # 여성, 미국식
    "adam":     "pNInz6obpgDQGcFmaJgB",  # 남성, 미국식
    "domi":     "AZnzlk1XvdvUeBnXmlld",  # 여성, 미국식
    "josh":     "TxGEqnHWrfWFTfGW9XjX",  # 남성, 미국식
    "bella":    "EXAVITQu4vr4xnSDxMaL",  # 여성, 미국식
    "elli":     "MF3mGyEYCl7XYWbV9V6O",  # 여성, 미국식
}

# 학습할 텍스트 변형 (발음·속도 다양화)
PHRASES = [
    "크랭크 오토",
    "크랭크 오토",
    "크랭크 오토",
    "크랭크 오토",
]

SAMPLES_PER_VOICE = 5   # 목소리당 샘플 수 (각 phrase × stability 변형)


async def generate_one(
    client: httpx.AsyncClient,
    voice_id: str,
    text: str,
    stability: float,
    similarity_boost: float,
) -> bytes:
    """MP3 bytes 반환."""
    resp = await client.post(
        f"{BASE_URL}/text-to-speech/{voice_id}/stream",
        headers={"xi-api-key": API_KEY, "Accept": "audio/mpeg"},
        json={
            "text": text,
            "model_id": "eleven_flash_v2_5",
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
            },
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.content


def mp3_to_wav_16k(mp3_bytes: bytes) -> np.ndarray:
    """MP3 → PCM int16 16kHz mono numpy array."""
    # ffmpeg subprocess로 변환
    import asyncio, subprocess
    result = subprocess.run(
        ["ffmpeg", "-i", "pipe:0", "-f", "s16le", "-ar", "16000", "-ac", "1",
         "-loglevel", "quiet", "pipe:1"],
        input=mp3_bytes, capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")
    return np.frombuffer(result.stdout, dtype=np.int16)


def save_wav(path: Path, audio: np.ndarray):
    path.parent.mkdir(parents=True, exist_ok=True)
    # 2초(32000샘플)로 맞춤 — openwakeword window size(16 frames)에 딱 맞음
    target_len = SR_TARGET * 2
    if len(audio) < target_len:
        audio = np.concatenate([np.zeros(target_len - len(audio), dtype=np.int16), audio])
    else:
        audio = audio[-target_len:]  # 뒷부분 2초 유지 (발화가 끝에 오도록)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR_TARGET)
        wf.writeframes(audio.tobytes())


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    existing = len(list(OUTPUT_DIR.glob("tts_*.wav")))
    print(f"기존 TTS 샘플: {existing}개\n")

    # stability 변형으로 같은 목소리에서 다양한 발음 생성
    stability_values = [0.3, 0.5, 0.7, 0.9, 0.5]
    similarity_values = [0.7, 0.7, 0.8, 0.6, 0.9]

    generated = 0
    async with httpx.AsyncClient() as client:
        for voice_name, voice_id in VOICES.items():
            print(f"[{voice_name}] 생성 중...")
            for i in range(SAMPLES_PER_VOICE):
                phrase = PHRASES[i % len(PHRASES)]
                stab = stability_values[i]
                sim = similarity_values[i]
                try:
                    mp3 = await generate_one(client, voice_id, phrase, stab, sim)
                    audio = mp3_to_wav_16k(mp3)
                    idx = existing + generated
                    path = OUTPUT_DIR / f"tts_{voice_name}_{i:02d}.wav"
                    save_wav(path, audio)
                    print(f"  ✅ {path.name}")
                    generated += 1
                except Exception as e:
                    print(f"  ⚠️  {voice_name} 샘플 {i} 실패: {e}")

    total = len(list(OUTPUT_DIR.glob("*.wav")))
    tts_count = len(list(OUTPUT_DIR.glob("tts_*.wav")))
    real_count = total - tts_count
    print(f"\n완료!")
    print(f"  실제 녹음: {real_count}개")
    print(f"  TTS 생성:  {tts_count}개  ({len(VOICES)}가지 목소리 × {SAMPLES_PER_VOICE}개)")
    print(f"  총 positive: {total}개")


if __name__ == "__main__":
    asyncio.run(main())
