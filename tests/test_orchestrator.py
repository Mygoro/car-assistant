"""Unit tests for core/orchestrator.py — no real API calls, uses a stub provider."""
import asyncio
import pytest
from collections import deque

from core.providers.base import Message, Delta
from core.orchestrator import classify_intent, Orchestrator, SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Stub provider that returns a fixed response without hitting the network
# ---------------------------------------------------------------------------

class _StubProvider:
    def __init__(self, reply: str = "테스트 응답"):
        self.model = "stub"
        self.last_messages: list[Message] = []
        self._reply = reply

    async def stream(self, messages: list[Message], tools: list[dict]):
        self.last_messages = messages
        yield Delta(text=self._reply)
        yield Delta(text="", is_final=True)


# ---------------------------------------------------------------------------
# Helper: build minimal cfg dict
# ---------------------------------------------------------------------------

def _make_cfg(history_turns: int = 3) -> dict:
    return {
        "llm": {
            "default_provider": "anthropic",
            "default_model": "claude-sonnet-4-6",
            "max_tokens": 100,
            "history_turns": history_turns,
        },
        "intent_routing": {
            "note.create": "anthropic/claude-sonnet-4-6",
            "calendar.read": "anthropic/claude-haiku-4-5-20251001",
            "calendar.write": "anthropic/claude-sonnet-4-6",
            "research": "anthropic/claude-sonnet-4-6",
            "simple_qa": "anthropic/claude-haiku-4-5-20251001",
            "offline_fallback": "ollama/qwen2.5:14b",
        },
    }


def _make_orchestrator(reply: str = "테스트 응답", history_turns: int = 3) -> tuple["Orchestrator", "_StubProvider"]:
    orch = Orchestrator(cfg=_make_cfg(history_turns), anthropic_api_key="dummy")
    stub = _StubProvider(reply=reply)
    # Replace real providers with stub
    orch._anthropic = stub
    orch._ollama = stub
    return orch, stub


# ---------------------------------------------------------------------------
# classify_intent
# ---------------------------------------------------------------------------

def test_classify_intent_note():
    assert classify_intent("오늘 강의 내용 메모해줘") == "note.create"

def test_classify_intent_note_record():
    assert classify_intent("이걸 기록해줘") == "note.create"

def test_classify_intent_calendar_read():
    assert classify_intent("내일 일정 알려줘") == "calendar.read"

def test_classify_intent_calendar_write():
    assert classify_intent("금요일 약속 캘린더에 추가해줘") == "calendar.write"

def test_classify_intent_research():
    assert classify_intent("MCP가 뭔지 알아봐줘") == "research"

def test_classify_intent_simple_qa():
    assert classify_intent("오늘 날씨 어때") == "simple_qa"


# ---------------------------------------------------------------------------
# Orchestrator.handle — basic response
# ---------------------------------------------------------------------------

def test_handle_returns_response():
    orch, stub = _make_orchestrator(reply="안녕하세요!")
    result = asyncio.run(orch.handle("안녕"))
    assert result == "안녕하세요!"


def test_handle_builds_system_message():
    orch, stub = _make_orchestrator()
    asyncio.run(orch.handle("테스트"))
    system_msgs = [m for m in stub.last_messages if m.role == "system"]
    assert len(system_msgs) == 1
    assert "음성 AI 어시스턴트" in system_msgs[0].content


def test_handle_appends_user_message():
    orch, stub = _make_orchestrator()
    asyncio.run(orch.handle("오늘 날씨 어때"))
    user_msgs = [m for m in stub.last_messages if m.role == "user"]
    assert any("오늘 날씨 어때" in m.content for m in user_msgs)


# ---------------------------------------------------------------------------
# History management
# ---------------------------------------------------------------------------

def test_history_grows_after_turns():
    orch, _ = _make_orchestrator()
    asyncio.run(orch.handle("첫 번째"))
    asyncio.run(orch.handle("두 번째"))
    # 2 turns = 4 messages in history (user+assistant × 2)
    assert len(orch._history) == 4


def test_history_capped_at_max_turns():
    history_turns = 2
    orch, _ = _make_orchestrator(history_turns=history_turns)
    for i in range(5):
        asyncio.run(orch.handle(f"발화 {i}"))
    assert len(orch._history) <= history_turns * 2


def test_history_included_in_next_messages():
    orch, stub = _make_orchestrator()
    asyncio.run(orch.handle("첫 번째 질문"))
    asyncio.run(orch.handle("두 번째 질문"))
    # 두 번째 호출 시 첫 번째 user/assistant 쌍이 히스토리에 포함되어야 함
    roles = [m.role for m in stub.last_messages]
    assert "user" in roles
    assert "assistant" in roles


# ---------------------------------------------------------------------------
# Reset
# ---------------------------------------------------------------------------

def test_reset_clears_history():
    orch, _ = _make_orchestrator()
    asyncio.run(orch.handle("히스토리에 넣을 발화"))
    assert len(orch._history) > 0
    asyncio.run(orch.handle("리셋"))
    assert len(orch._history) == 0


def test_reset_response_text():
    orch, _ = _make_orchestrator()
    result = asyncio.run(orch.handle("새로 시작해"))
    assert "초기화" in result


# ---------------------------------------------------------------------------
# stream_handle — delta streaming
# ---------------------------------------------------------------------------

def test_stream_handle_yields_deltas():
    orch, stub = _make_orchestrator(reply="스트리밍 테스트")

    async def _collect():
        parts = []
        async for delta in orch.stream_handle("스트리밍 확인"):
            parts.append(delta)
        return parts

    deltas = asyncio.run(_collect())
    texts = [d.text for d in deltas if d.text]
    assert "스트리밍 테스트" in "".join(texts)
    assert any(d.is_final for d in deltas)


def test_stream_handle_updates_history():
    orch, _ = _make_orchestrator(reply="응답")

    async def _run():
        async for _ in orch.stream_handle("발화"):
            pass

    asyncio.run(_run())
    assert len(orch._history) == 2  # user + assistant


# ---------------------------------------------------------------------------
# Provider routing
# ---------------------------------------------------------------------------

def test_routing_selects_model():
    orch, stub = _make_orchestrator()
    asyncio.run(orch.handle("일정 알려줘"))  # calendar.read → haiku
    assert stub.model == "claude-haiku-4-5-20251001"


def test_routing_default_for_simple_qa():
    orch, stub = _make_orchestrator()
    asyncio.run(orch.handle("안녕"))  # simple_qa → haiku
    assert stub.model == "claude-haiku-4-5-20251001"
