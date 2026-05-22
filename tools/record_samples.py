#!/usr/bin/env python
"""
wake word 학습용 샘플 녹음 도구.

사용법:
  # "hey otto" 양성 샘플 녹음
  uv run tools/record_samples.py --type positive

  # 그 외 음성/소음 음성 샘플 녹음
  uv run tools/record_samples.py --type negative

  # 마이크 목록 확인
  uv run tools/record_samples.py --list-devices
"""

import argparse
import wave
import time
from pathlib import Path

import numpy as np
import sounddevice as sd

SR = 16000
POSITIVE_DURATION = 2   # 초 — 2s 클립 = 정확히 16 embedding frames (openwakeword window size)
NEGATIVE_DURATION = 3   # 초 — 더 긴 클립으로 window 다수 확보

TIPS_POSITIVE = """
[ 녹음 팁 ]
- 각 클립: Enter → 1초 묵음 → "hey otto" 발화 → 자동 종료
- 자연스러운 속도와 발음으로 말하기 (너무 또박또박 X)
- 다양한 볼륨/톤으로 녹음할수록 모델이 강건해집니다
- 차량 내 마이크와 동일한 거리에서 녹음하면 더 좋습니다
- 목표: 최소 20개, 권장 30개
"""

TIPS_NEGATIVE = """
[ 녹음 팁 ]
- 각 클립: Enter → 3초간 "hey otto"가 아닌 발화 또는 소음
- 예시: "안녕", "오늘 날씨 어때", "길 안내 시작", 엔진 소음, 음악
- "hey auto", "hey otter" 같은 유사 발음도 포함하면 오탐 감소
- 조용한 침묵만 녹음하는 클립도 몇 개 포함하세요
- 목표: 최소 20개, 권장 30개
"""


def list_devices():
    print(sd.query_devices())


def check_not_silent(audio: np.ndarray, threshold: int = 200) -> bool:
    return int(np.abs(audio).max()) > threshold


def record_one(path: Path, duration: int, sample_idx: int, total: int) -> bool:
    print(f"\n[{sample_idx}/{total}] Enter를 누르면 {duration}초 녹음 시작...")
    input()
    print("  ● REC", end="", flush=True)
    audio = sd.rec(int(duration * SR), samplerate=SR, channels=1, dtype='int16')
    for _ in range(duration):
        time.sleep(1)
        print(".", end="", flush=True)
    sd.wait()
    print(" 완료")

    audio = audio.flatten()
    if not check_not_silent(audio):
        print("  ⚠️  소리가 감지되지 않았습니다. 마이크를 확인하고 다시 녹음합니다.")
        return False

    with wave.open(str(path), 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(audio.tobytes())
    print(f"  저장됨: {path.name}")
    return True


def main():
    parser = argparse.ArgumentParser(description="wake word 학습 샘플 녹음")
    parser.add_argument('--type', choices=['positive', 'negative'])
    parser.add_argument('--count', type=int, default=30, help="녹음할 샘플 수 (기본 30)")
    parser.add_argument('--list-devices', action='store_true', help="마이크 목록 출력 후 종료")
    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        return

    if not args.type:
        parser.error("--type positive 또는 --type negative 를 지정하세요")

    duration = POSITIVE_DURATION if args.type == 'positive' else NEGATIVE_DURATION
    target_dir = Path(f"wake_word/training_data/{args.type}")
    target_dir.mkdir(parents=True, exist_ok=True)

    existing = sorted(target_dir.glob('*.wav'))
    start_idx = len(existing)

    print(f"\n=== {args.type.upper()} 샘플 녹음 ===")
    print(TIPS_POSITIVE if args.type == 'positive' else TIPS_NEGATIVE)
    print(f"기존 샘플: {start_idx}개 | 이번 녹음: {args.count}개")

    recorded = 0
    i = 0
    while recorded < args.count:
        path = target_dir / f"sample_{start_idx + recorded:03d}.wav"
        ok = record_one(path, duration, recorded + 1, args.count)
        if ok:
            recorded += 1
        i += 1
        if i > args.count * 3:
            print("너무 많이 재시도했습니다. 마이크 설정을 확인하세요.")
            break

    total = len(list(target_dir.glob('*.wav')))
    print(f"\n완료! {args.type} 샘플 누계: {total}개")
    if args.type == 'positive' and total < 15:
        print("⚠️  positive 샘플이 15개 미만입니다. 더 녹음하는 것을 권장합니다.")
    if args.type == 'negative' and total < 15:
        print("⚠️  negative 샘플이 15개 미만입니다. 더 녹음하는 것을 권장합니다.")


if __name__ == '__main__':
    main()
