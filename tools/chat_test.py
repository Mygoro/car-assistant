"""간이 LLM 테스터 — 마이크 없이 트랜스크립트를 직접 입력해 Phase 4 파이프라인 검증.

사용법:
    uv run tools/chat_test.py
    uv run tools/chat_test.py --no-stream   # 스트리밍 없이 완성 응답만 출력

출력 형식 (매 턴):
    [intent: <인텐트> → <모델>]
    [voice] <voice_response>
    [text]  <text_response>
"""
import argparse
import asyncio
import io
import os
import sys
from pathlib import Path

# Windows 콘솔 UTF-8 강제 적용
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 프로젝트 루트를 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from dotenv import load_dotenv

from core.orchestrator import Orchestrator, classify_intent
from core.tts import ElevenLabsTTS, speak_local

load_dotenv()

with open("config.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)

GREY   = "\033[90m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def _print_header():
    print(f"\n{BOLD}=== Otto LLM 간이 테스터 ==={RESET}")
    print(f"{GREY}입력: 테스트할 발화  |  !reset: 히스토리 초기화  |  !quit / Ctrl-C: 종료{RESET}\n")


def _print_turn(intent: str, route: str, voice: str, text: str):
    print(f"{GREY}[intent: {intent} -> {route}]{RESET}")
    if not voice and not text:
        print(f"{GREY}[skip] 두 필드 모두 빈 문자열 — TTS·게시 생략{RESET}\n")
        return
    char_count = len(voice)
    warn = f" {YELLOW}(!){RESET}" if char_count > 100 else ""
    print(f"{GREEN}[voice] ({char_count}자){warn} {voice}{RESET}")
    print(f"{CYAN}[text]  {text}{RESET}\n")


async def _stream_turn(orch: Orchestrator, transcript: str, tts_client: ElevenLabsTTS | None = None):
    intent = classify_intent(transcript)
    route = cfg.get("intent_routing", {}).get(intent) or cfg.get("intent_routing", {}).get("default", "?")
    parts: list[str] = []
    async for delta in orch.stream_handle(transcript):
        if delta.text:
            parts.append(delta.text)
    voice = "".join(parts)
    char_count = len(voice)
    warn = f" {YELLOW}(!){RESET}" if char_count > 100 else ""
    print(f"{GREY}[intent: {intent} -> {route}]{RESET}")
    if not voice:
        print(f"{GREY}[skip] voice_response 빈 문자열{RESET}\n")
    else:
        print(f"{GREEN}[voice] ({char_count}자){warn} {voice}{RESET}\n")
        if tts_client:
            await speak_local(tts_client, voice)


async def _full_turn(orch: Orchestrator, transcript: str, tts_client: ElevenLabsTTS | None = None):
    intent = classify_intent(transcript)
    route = cfg.get("intent_routing", {}).get(intent) or cfg.get("intent_routing", {}).get("default", "?")
    voice, text = await orch.handle(transcript)
    _print_turn(intent, route, voice, text)
    if tts_client and voice:
        await speak_local(tts_client, voice)


async def main(stream: bool, tts_enabled: bool):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY가 .env에 없습니다.")
        sys.exit(1)

    tts_client: ElevenLabsTTS | None = None
    if tts_enabled:
        el_key = os.environ.get("ELEVENLABS_API_KEY", "")
        el_voice = os.environ.get("ELEVENLABS_VOICE_ID", "")
        if not el_key or not el_voice:
            print("⚠️  ELEVENLABS_API_KEY 또는 ELEVENLABS_VOICE_ID가 .env에 없습니다.")
            sys.exit(1)
        tts_client = ElevenLabsTTS(
            api_key=el_key,
            voice_id=el_voice,
            model=cfg["tts"]["model"],
        )
        print(f"{GREY}[TTS 활성화 — ElevenLabs {cfg['tts']['model']}]{RESET}\n")

    orch = Orchestrator(cfg=cfg, anthropic_api_key=api_key)
    _print_header()

    while True:
        try:
            transcript = input(f"{CYAN}🎤 > {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break

        if not transcript:
            continue
        if transcript in ("!quit", "!exit", "q"):
            print("종료합니다.")
            break
        if transcript == "!reset":
            orch._history.clear()
            print(f"{GREY}[히스토리 초기화됨]{RESET}\n")
            continue
        if transcript == "!history":
            if not orch._history:
                print(f"{GREY}[히스토리 없음]{RESET}\n")
            else:
                for i, m in enumerate(orch._history):
                    print(f"{GREY}[{i}] {m.role}: {m.content[:60]}...{RESET}")
                print()
            continue

        try:
            if stream:
                await _stream_turn(orch, transcript, tts_client)
            else:
                await _full_turn(orch, transcript, tts_client)
        except Exception as e:
            print(f"⚠️  오류: {e}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Otto LLM 간이 테스터")
    parser.add_argument("--no-stream", action="store_true", help="스트리밍 없이 완성 응답 출력")
    parser.add_argument("--tts", action="store_true", help="voice_response를 로컬 스피커로 재생")
    args = parser.parse_args()
    asyncio.run(main(stream=not args.no_stream, tts_enabled=args.tts))
