"""Phase 4: LLM 텍스트 응답 오케스트레이터.

인텐트 분류 → 프로바이더 선택 → 스트리밍 응답 → 히스토리 관리.
"""
import logging
from collections import deque

from .providers.base import Message, Delta
from .providers.anthropic import AnthropicProvider
from .providers.ollama import OllamaProvider

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """당신은 사용자를 보조하는 음성 AI 어시스턴트입니다.

사용자 컨텍스트:
- 연세대학교 재학생, DigiTools/AI Agents 수강 중
- 한국어로 주로 소통하며 영어 전문 용어도 사용
- 주요 도구: Notion, Google Calendar, Claude Code, ElevenLabs, Krita MCP

응답 지침:
- 응답은 음성으로 전달된다
- 마크다운 형식(##, **, ```)을 사용하지 않는다
- 목록은 자연스러운 문장으로 표현한다
- 불필요한 서두와 반복을 생략한다
- 필요한 정보는 생략하지 않고 정확하게 전달한다""".strip()

_RESET_KEYWORDS = {"새로 시작해", "새로시작해", "리셋", "초기화", "대화 초기화"}


def classify_intent(transcript: str) -> str:
    t = transcript.strip()
    if any(kw in t for kw in ("기록", "메모", "노트", "저장")):
        return "note.create"
    if any(kw in t for kw in ("일정", "캘린더", "약속", "몇 시", "언제")):
        if any(kw in t for kw in ("추가", "등록", "넣어", "잡아")):
            return "calendar.write"
        return "calendar.read"
    if any(kw in t for kw in ("찾아", "검색", "알아봐", "뭐야", "뭔지")):
        return "research"
    return "simple_qa"


class Orchestrator:
    def __init__(self, cfg: dict, anthropic_api_key: str):
        llm_cfg = cfg.get("llm", {})
        self._default_provider_name = llm_cfg.get("default_provider", "anthropic")
        self._default_model = llm_cfg.get("default_model", "claude-sonnet-4-6")
        self._max_tokens = llm_cfg.get("max_tokens", 1000)
        self._history_turns = llm_cfg.get("history_turns", 10)
        self._routing: dict[str, str] = cfg.get("intent_routing", {})

        self._anthropic_key = anthropic_api_key
        self._history: deque[Message] = deque()

        # 프로바이더 인스턴스는 봇 시작 시 한 번만 생성
        self._anthropic = AnthropicProvider(
            api_key=anthropic_api_key,
            model=self._default_model,
            max_tokens=self._max_tokens,
        )
        # Ollama는 오프라인 폴백 용도(Phase 8). 모델명은 routing에서 읽음.
        ollama_model = self._parse_model(
            self._routing.get("offline_fallback", "ollama/qwen2.5:14b")
        )[1]
        self._ollama = OllamaProvider(model=ollama_model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def handle(self, transcript: str):
        """트랜스크립트 → LLM 스트리밍 → 완성된 응답 문자열 반환."""
        if any(kw in transcript for kw in _RESET_KEYWORDS):
            self._history.clear()
            log.info("Conversation history reset")
            return "대화 기록을 초기화했어요."

        intent = classify_intent(transcript)
        provider = self._get_provider(intent)
        log.info("Intent: %s, Provider: %s/%s", intent, provider.model if hasattr(provider, 'model') else '?', type(provider).__name__)

        messages = self._build_messages(transcript)
        full_response = await self._stream_to_str(provider, messages)

        if full_response:
            self._push_history(Message("user", transcript))
            self._push_history(Message("assistant", full_response))

        return full_response

    async def stream_handle(self, transcript: str):
        """트랜스크립트 → Delta 비동기 제너레이터.

        Phase 5 TTS 파이프라인에서 사용. 응답 완료 후 히스토리 자동 업데이트.
        """
        if any(kw in transcript for kw in _RESET_KEYWORDS):
            self._history.clear()
            log.info("Conversation history reset")
            yield Delta(text="대화 기록을 초기화했어요.", is_final=True)
            return

        intent = classify_intent(transcript)
        provider = self._get_provider(intent)
        messages = self._build_messages(transcript)

        collected: list[str] = []
        async for delta in provider.stream(messages, tools=[]):
            if delta.text:
                collected.append(delta.text)
            yield delta

        full = "".join(collected)
        if full:
            self._push_history(Message("user", transcript))
            self._push_history(Message("assistant", full))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_messages(self, transcript: str) -> list[Message]:
        msgs: list[Message] = [Message("system", SYSTEM_PROMPT)]
        msgs.extend(self._history)
        msgs.append(Message("user", transcript))
        return msgs

    def _push_history(self, msg: Message):
        self._history.append(msg)
        # 히스토리는 턴 단위(user+assistant 쌍). 최대 history_turns 턴 유지.
        max_msgs = self._history_turns * 2
        while len(self._history) > max_msgs:
            self._history.popleft()

    def _get_provider(self, intent: str) -> AnthropicProvider | OllamaProvider:
        route = self._routing.get(intent, "")
        provider_name, model = self._parse_model(route or f"anthropic/{self._default_model}")
        if provider_name == "ollama":
            self._ollama.model = model
            return self._ollama
        # anthropic 계열 — 모델이 routing에 따라 다를 수 있으므로 동적 설정
        self._anthropic.model = model
        return self._anthropic

    @staticmethod
    def _parse_model(route: str) -> tuple[str, str]:
        """'anthropic/claude-sonnet-4-6' → ('anthropic', 'claude-sonnet-4-6')."""
        if "/" in route:
            provider, model = route.split("/", 1)
            return provider.strip(), model.strip()
        return "anthropic", route.strip()

    @staticmethod
    async def _stream_to_str(provider, messages: list[Message]) -> str:
        parts: list[str] = []
        async for delta in provider.stream(messages, tools=[]):
            if delta.text:
                parts.append(delta.text)
        return "".join(parts)
