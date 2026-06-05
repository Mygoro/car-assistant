"""run_voice_streaming(⑥ overlap) 파서 정확성 — 네트워크 없이 mock provider로 검증.

직접 실행: uv run python tests/test_voice_streaming.py
(기존 test_orchestrator.py는 스테일하므로 pytest 전체 수집 대신 이 파일만 단독 실행)
"""
import asyncio
import json

from core.providers.base import Delta
from core.orchestrator import Orchestrator


class _MockProvider:
    """고정 JSON 응답을 chunk 크기로 쪼개 스트리밍하는 가짜 프로바이더."""
    def __init__(self, raw: str, chunk: int = 1):
        self.model = "mock"
        self._raw = raw
        self._chunk = chunk

    async def stream(self, messages, tools):
        for i in range(0, len(self._raw), self._chunk):
            yield Delta(text=self._raw[i:i + self._chunk])
        yield Delta(text="", is_final=True)


_CFG = {
    "llm": {"default_model": "claude-sonnet-4-6", "max_tokens": 100, "history_turns": 3},
    "intent_routing": {"default": "anthropic/claude-sonnet-4-6",
                       "offline_fallback": "ollama/qwen2.5:14b"},
}


async def _collect(raw: str, chunk: int):
    orch = Orchestrator(cfg=_CFG, anthropic_api_key="dummy")
    orch._anthropic = _MockProvider(raw, chunk)
    events = []
    async for stage, content in orch.run_voice_streaming("테스트 질문"):
        events.append((stage, content))
    return events


def _check(raw: str, chunk: int, expect_voice: str, expect_text: str, label: str):
    events = asyncio.run(_collect(raw, chunk))
    voice = "".join(c for s, c in events if s == "voice_chunk")
    voice_end_count = sum(1 for s, _ in events if s == "voice_end")
    text_events = [c for s, c in events if s == "text"]

    # 1) voice_chunk 합 == 기대 디코딩 voice
    assert voice == expect_voice, f"[{label}] voice mismatch: {voice!r} != {expect_voice!r}"
    # 2) voice_end 정확히 1회
    assert voice_end_count == 1, f"[{label}] voice_end count = {voice_end_count}"
    # 3) text 정확히 1회 + 값 일치
    assert len(text_events) == 1, f"[{label}] text events = {len(text_events)}"
    assert text_events[0] == expect_text, f"[{label}] text mismatch: {text_events[0]!r}"
    # 4) 순서: 모든 voice_chunk → voice_end → text (voice_end가 마지막 voice_chunk 뒤, text 앞)
    stages = [s for s, _ in events]
    assert stages.index("voice_end") < stages.index("text"), f"[{label}] order: voice_end after text"
    if "voice_chunk" in stages:
        last_chunk = len(stages) - 1 - stages[::-1].index("voice_chunk")
        assert last_chunk < stages.index("voice_end"), f"[{label}] voice_chunk after voice_end"
    print(f"  PASS [{label}] (chunk={chunk}) voice={voice!r}")


def main():
    # 케이스별 (raw JSON, 기대 voice, 기대 text)
    cases = [
        (
            '{"voice_response": "안녕하세요. 반가워요.", "text_response": "상세 답변입니다."}',
            "안녕하세요. 반가워요.", "상세 답변입니다.", "normal",
        ),
        (
            # 이스케이프: \" 와 \n 포함 (경계에서 쪼개지는 케이스를 chunk=1로 강제)
            '{"voice_response": "그는 \\"네\\"라고\\n답했어요.", "text_response": "T"}',
            '그는 "네"라고\n답했어요.', "T", "escapes",
        ),
        (
            '{"voice_response": "", "text_response": "빈 보이스"}',
            "", "빈 보이스", "empty-voice",
        ),
        (
            # 코드펜스로 감싼 응답 (Claude가 가끔 그럼)
            '```json\n{"voice_response": "펜스 안 응답", "text_response": "펜스 텍스트"}\n```',
            "펜스 안 응답", "펜스 텍스트", "code-fence",
        ),
        (
            # BMP \u 이스케이프가 경계에서 쪼개짐 (가 = 가)
            '{"voice_response": "코드\\uAC00값", "text_response": "x"}',
            "코드가값", "x", "unicode-escape",
        ),
    ]

    print("run_voice_streaming 파서 테스트")
    for raw, ev, et, label in cases:
        # 여러 chunk 크기로 (1글자 / 3글자 / 통짜) 모두 동일 결과여야 함
        for chunk in (1, 3, len(raw)):
            _check(raw, chunk, ev, et, label)

    print("\nALL VOICE-STREAMING PARSER TESTS PASSED")


if __name__ == "__main__":
    main()
