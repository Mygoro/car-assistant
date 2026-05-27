"""Phase 4: LLM 텍스트 응답 오케스트레이터.

인텐트 분류 → 프로바이더 선택 → 스트리밍 응답 → JSON 파싱 → 히스토리 관리.
"""
import json
import logging
import re
from collections import deque
from pathlib import Path

from .providers.base import Message, Delta
from .providers.anthropic import AnthropicProvider
from .providers.ollama import OllamaProvider

log = logging.getLogger(__name__)

_RESET_KEYWORDS = {"새로 시작해", "새로시작해", "리셋", "초기화", "대화 초기화"}

# voice_response 값이 완성된 시점을 스트림 중에 감지
_VOICE_RE = re.compile(r'"voice_response"\s*:\s*"((?:[^"\\]|\\.)*)"')


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def build_system_prompt() -> str:
    """Load template and inject current memory.md content."""
    template_path = Path("core/system_prompt_template.txt")
    memory_path = Path("core/memory.md")

    template = template_path.read_text(encoding="utf-8")
    memory = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""

    return template.replace("{MEMORY_MD_INJECTION_POINT}", memory)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def parse_dual_response(raw: str) -> tuple[str, str]:
    """Parse JSON response into (voice_response, text_response).

    Falls back to using raw text in both fields if parsing fails.
    """
    try:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
        obj = json.loads(cleaned)
        voice = obj.get("voice_response", "")
        text = obj.get("text_response", "")
        return voice, text
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        log.warning("JSON parse failed: %s. Raw: %s", e, raw[:100])
        return raw[:100], raw


def validate_voice_length(voice: str) -> str:
    """Log warning if voice exceeds 100 chars, but do not truncate."""
    if len(voice) > 100:
        log.warning(
            "voice_response exceeds 100 chars (%d): %s...", len(voice), voice[:60]
        )
    return voice


# ---------------------------------------------------------------------------
# Intent classification
# ---------------------------------------------------------------------------

def classify_intent(transcript: str) -> str:
    t = transcript.strip()

    trivial_patterns = ["몇 시", "지금 시각", "안녕", "하이", "고마워",
                        "고맙다", "확인", "응", "네"]
    if any(p in t for p in trivial_patterns) and len(t) < 15:
        return "trivial"

    if any(kw in t for kw in ["깊이 생각", "자세히 분석", "꼼꼼히"]):
        return "complex_reasoning"

    return "default"


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class Orchestrator:
    def __init__(self, cfg: dict, anthropic_api_key: str):
        llm_cfg = cfg.get("llm", {})
        self._default_model = llm_cfg.get("default_model", "claude-sonnet-4-6")
        self._max_tokens = llm_cfg.get("max_tokens", 1000)
        self._history_turns = llm_cfg.get("history_turns", 10)
        self._routing: dict[str, str] = cfg.get("intent_routing", {})

        self._history: deque[Message] = deque()

        # 프로바이더 인스턴스는 봇 시작 시 한 번만 생성
        self._anthropic = AnthropicProvider(
            api_key=anthropic_api_key,
            model=self._default_model,
            max_tokens=self._max_tokens,
        )
        ollama_model = self._parse_model(
            self._routing.get("offline_fallback", "ollama/qwen2.5:14b")
        )[1]
        self._ollama = OllamaProvider(model=ollama_model)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def handle(self, transcript: str) -> tuple[str, str]:
        """트랜스크립트 → (voice_response, text_response).

        두 필드 모두 빈 문자열이면 TTS·Discord 게시 모두 skip.
        """
        if any(kw in transcript for kw in _RESET_KEYWORDS):
            self._history.clear()
            log.info("Conversation history reset")
            return "대화 기록을 초기화했어요.", "(히스토리 초기화)"

        intent = classify_intent(transcript)
        provider = self._get_provider(intent)
        log.info("Intent: %s | model: %s", intent, provider.model)

        messages = self._build_messages(transcript)
        raw = await self._stream_to_str(provider, messages)
        log.debug("Raw LLM response: %.200s", raw)

        voice, text = parse_dual_response(raw)
        voice = validate_voice_length(voice)

        if voice or text:
            self._push_history(Message("user", transcript))
            self._push_history(Message("assistant", raw))

        return voice, text

    async def stream_handle(self, transcript: str):
        """트랜스크립트 → Delta 제너레이터 (Phase 5 TTS 파이프라인용).

        JSON 포맷 응답은 전체 수신 후 파싱해야 하므로 누적 후 voice_response만 방출.
        """
        if any(kw in transcript for kw in _RESET_KEYWORDS):
            self._history.clear()
            log.info("Conversation history reset")
            yield Delta(text="대화 기록을 초기화했어요.", is_final=True)
            return

        intent = classify_intent(transcript)
        provider = self._get_provider(intent)
        messages = self._build_messages(transcript)

        raw = await self._stream_to_str(provider, messages)
        voice, text = parse_dual_response(raw)
        voice = validate_voice_length(voice)

        if voice or text:
            self._push_history(Message("user", transcript))
            self._push_history(Message("assistant", raw))

        # Phase 5: voice_response를 TTS 파이프라인에 전달
        if voice:
            yield Delta(text=voice)
        yield Delta(text="", is_final=True)

    async def run_voice_first(self, transcript: str):
        """Voice-first 파이프라인.

        Yields:
            ('voice', str) — voice_response 완성 즉시 (TTS 시작 신호)
            ('text',  str) — 전체 응답 완성 후 (Discord 게시 신호)
        """
        if any(kw in transcript for kw in _RESET_KEYWORDS):
            self._history.clear()
            log.info("Conversation history reset")
            yield "voice", "대화 기록을 초기화했어요."
            yield "text", "(히스토리 초기화)"
            return

        intent = classify_intent(transcript)
        provider = self._get_provider(intent)
        log.info("Intent: %s | model: %s", intent, provider.model)
        messages = self._build_messages(transcript)

        buffer = ""
        voice_emitted = False

        async for delta in provider.stream(messages, tools=[]):
            if delta.text:
                buffer += delta.text
                if not voice_emitted:
                    m = _VOICE_RE.search(buffer)
                    if m:
                        try:
                            voice = json.loads(f'"{m.group(1)}"')
                        except json.JSONDecodeError:
                            voice = m.group(1)
                        voice = validate_voice_length(voice)
                        voice_emitted = True
                        yield "voice", voice

        # 전체 응답 완성 — text_response 파싱
        voice_full, text = parse_dual_response(buffer)

        if not voice_emitted:
            yield "voice", validate_voice_length(voice_full)

        if voice_full or text:
            self._push_history(Message("user", transcript))
            self._push_history(Message("assistant", buffer))

        yield "text", text

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_messages(self, transcript: str) -> list[Message]:
        msgs: list[Message] = [Message("system", build_system_prompt())]
        msgs.extend(self._history)
        msgs.append(Message("user", transcript))
        return msgs

    def _push_history(self, msg: Message):
        self._history.append(msg)
        max_msgs = self._history_turns * 2
        while len(self._history) > max_msgs:
            self._history.popleft()

    def _get_provider(self, intent: str) -> AnthropicProvider | OllamaProvider:
        route = (
            self._routing.get(intent)
            or self._routing.get("default", f"anthropic/{self._default_model}")
        )
        provider_name, model = self._parse_model(route)
        if provider_name == "ollama":
            self._ollama.model = model
            return self._ollama
        self._anthropic.model = model
        return self._anthropic

    @staticmethod
    def _parse_model(route: str) -> tuple[str, str]:
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
