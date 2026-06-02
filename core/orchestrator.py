"""Phase 6: LLM 텍스트 응답 오케스트레이터 + MCP/native 툴 통합.

인텐트 분류 → 프로바이더 선택 → (툴 루프) → 스트리밍 응답 → JSON 파싱 → 히스토리.
"""
import asyncio
import json
import logging
import os
import re
from collections import deque
from contextlib import AsyncExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Awaitable, Optional

from .providers.base import Message, Delta
from .providers.anthropic import AnthropicProvider
from .providers.ollama import OllamaProvider

log = logging.getLogger(__name__)

_RESET_KEYWORDS = {"새로 시작해", "새로시작해", "리셋", "초기화", "대화 초기화"}

# voice_response 값이 완성된 시점을 스트림 중에 감지
_VOICE_RE = re.compile(r'"voice_response"\s*:\s*"((?:[^"\\]|\\.)*)"')


# ---------------------------------------------------------------------------
# ToolHandle — MCP와 native 툴을 하나의 인터페이스로 통합
# ---------------------------------------------------------------------------

@dataclass
class ToolHandle:
    name: str
    schema: dict                          # Claude tools 파라미터용
    kind: str                             # "mcp" | "native"
    mcp_server: Optional[str] = None      # kind=="mcp"일 때
    native_fn: Optional[Callable[[dict], Awaitable[str]]] = None  # kind=="native"일 때


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

def build_system_prompt() -> str:
    template_path = Path("core/system_prompt_template.txt")
    memory_path = Path("core/memory.md")

    template = template_path.read_text(encoding="utf-8")
    memory = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""

    return template.replace("{MEMORY_MD_INJECTION_POINT}", memory)


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def parse_dual_response(raw: str) -> tuple[str, str]:
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
    if len(voice) > 100:
        log.warning("voice_response exceeds 100 chars (%d): %s...", len(voice), voice[:60])
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
        self._cfg = cfg
        llm_cfg = cfg.get("llm", {})
        self._default_model = llm_cfg.get("default_model", "claude-sonnet-4-6")
        self._max_tokens = llm_cfg.get("max_tokens", 1000)
        self._history_turns = llm_cfg.get("history_turns", 10)
        self._routing: dict[str, str] = cfg.get("intent_routing", {})

        self._history: deque[Message] = deque()

        self._anthropic = AnthropicProvider(
            api_key=anthropic_api_key,
            model=self._default_model,
            max_tokens=self._max_tokens,
        )
        ollama_model = self._parse_model(
            self._routing.get("offline_fallback", "ollama/qwen2.5:14b")
        )[1]
        self._ollama = OllamaProvider(model=ollama_model)

        # 툴 레지스트리
        self._tools: dict[str, ToolHandle] = {}
        self._sessions: dict[str, object] = {}  # server_name → ClientSession
        self._exit_stack: Optional[AsyncExitStack] = None

        # tool_use 설정
        tool_cfg = cfg.get("tool_use", {})
        self._max_iterations = tool_cfg.get("max_iterations", 5)
        self._tool_timeout_s = tool_cfg.get("tool_timeout_s", 15)

    # ------------------------------------------------------------------
    # 시작 / 종료
    # ------------------------------------------------------------------

    async def start(self):
        """봇 시작 시 1회 호출. MCP 서버 기동 + native 툴 등록."""
        await self._start_mcp()
        await self._start_native()
        log.info("총 툴 %d개 등록 (MCP %d + native %d)",
                 len(self._tools),
                 sum(1 for t in self._tools.values() if t.kind == "mcp"),
                 sum(1 for t in self._tools.values() if t.kind == "native"))

    async def aclose(self):
        """봇 종료 시 MCP subprocess 정리."""
        if self._exit_stack:
            await self._exit_stack.aclose()

    # ------------------------------------------------------------------
    # MCP 세션 초기화
    # ------------------------------------------------------------------

    async def _start_mcp(self):
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        self._exit_stack = AsyncExitStack()
        mcp_cfg = self._cfg.get("mcp_servers", {})

        for server_name, scfg in mcp_cfg.items():
            try:
                env = {k: os.path.expandvars(v) for k, v in scfg.get("env", {}).items()}
                params = StdioServerParameters(
                    command=scfg["command"][0],
                    args=scfg["command"][1:],
                    env={**os.environ, **env},
                )
                read, write = await self._exit_stack.enter_async_context(stdio_client(params))
                session = await self._exit_stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                tools_result = await session.list_tools()
                self._sessions[server_name] = session
                for tool in tools_result.tools:
                    self._tools[tool.name] = ToolHandle(
                        name=tool.name,
                        schema={
                            "name": tool.name,
                            "description": tool.description,
                            "input_schema": tool.inputSchema,
                        },
                        kind="mcp",
                        mcp_server=server_name,
                    )
                log.info("MCP '%s' 연결 완료, 툴 %d개", server_name, len(tools_result.tools))
            except Exception as e:
                log.error("MCP '%s' 연결 실패: %s — 건너뜀", server_name, e)

    # ------------------------------------------------------------------
    # Native 툴 등록
    # ------------------------------------------------------------------

    def _register_native(self, name: str, description: str, input_schema: dict, fn):
        self._tools[name] = ToolHandle(
            name=name,
            schema={"name": name, "description": description, "input_schema": input_schema},
            kind="native",
            native_fn=fn,
        )

    async def _start_native(self):
        from .native_tools.calendar import get_calendar_events
        from .native_tools.vehicle import get_vehicle_status
        from .native_tools.kakao import search_nearby_places, reverse_geocode

        self._register_native(
            name="get_calendar_events",
            description="사용자의 Google Calendar 일정을 조회한다. 날짜 범위를 받아 해당 기간 일정 목록을 반환.",
            input_schema={
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "description": "ISO date, e.g. 2026-06-02"},
                    "end_date": {"type": "string", "description": "ISO date (생략 시 start_date + 7일)"},
                },
                "required": ["start_date"],
            },
            fn=get_calendar_events,
        )
        self._register_native(
            name="get_vehicle_status",
            description="차량의 연료 잔여 주행거리(DTE), 누적 주행거리, 마지막 주차 위치를 조회.",
            input_schema={"type": "object", "properties": {}},
            fn=get_vehicle_status,
        )
        self._register_native(
            name="search_nearby_places",
            description="현재 위치 기준 주변 장소를 검색. 주유소, 충전소, 맛집 등.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색어, e.g. 주유소"},
                    "lon": {"type": "number", "description": "경도"},
                    "lat": {"type": "number", "description": "위도"},
                    "radius_m": {"type": "integer", "description": "검색 반경 미터 (기본 5000)"},
                },
                "required": ["query", "lon", "lat"],
            },
            fn=search_nearby_places,
        )
        self._register_native(
            name="reverse_geocode",
            description="GPS 좌표(위도, 경도)를 한국어 주소로 변환.",
            input_schema={
                "type": "object",
                "properties": {
                    "lon": {"type": "number"},
                    "lat": {"type": "number"},
                },
                "required": ["lon", "lat"],
            },
            fn=reverse_geocode,
        )

    # ------------------------------------------------------------------
    # 통합 툴 호출
    # ------------------------------------------------------------------

    async def _call_tool_safe(self, name: str, arguments: dict) -> str:
        handle = self._tools.get(name)
        if not handle:
            return f"[Tool error: '{name}' 미등록]"
        try:
            if handle.kind == "mcp":
                result = await asyncio.wait_for(
                    self._sessions[handle.mcp_server].call_tool(name, arguments),
                    timeout=self._tool_timeout_s,
                )
                texts = [c.text for c in result.content if hasattr(c, "text")]
                return "\n".join(texts) if texts else "[Tool returned no text]"
            else:
                return await asyncio.wait_for(
                    handle.native_fn(arguments),
                    timeout=self._tool_timeout_s,
                )
        except asyncio.TimeoutError:
            return f"[Tool '{name}' timed out after {self._tool_timeout_s}s]"
        except Exception as e:
            log.error("Tool '%s' error: %s", name, e)
            return f"[Tool '{name}' error: {e}]"

    def _all_schemas(self) -> list[dict]:
        return [t.schema for t in self._tools.values()]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_voice_first(self, transcript: str):
        """Voice-first 파이프라인.

        Yields:
            ('voice',  str) — voice_response 완성 즉시 (TTS 시작 신호)
            ('text',   str) — 전체 응답 완성 후 (Discord 게시 신호)
            ('filler', str) — 툴 호출 전 (filler 재생 신호, 첫 회만)
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

        # trivial이거나 툴 없으면 기존 스트리밍 경로 (TTS 지연 최소)
        if intent == "trivial" or not self._tools:
            async for stage, content in self._stream_voice_first(provider, messages):
                yield stage, content
            self._push_history(Message("user", transcript))
            return

        # 툴 사용 경로
        async for stage, content in self._tool_voice_first(provider, messages, transcript):
            yield stage, content

    # ------------------------------------------------------------------
    # 스트리밍 경로 (trivial / 툴 없음)
    # ------------------------------------------------------------------

    async def _stream_voice_first(self, provider, messages: list[Message]):
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

        voice_full, text = parse_dual_response(buffer)

        if not voice_emitted:
            yield "voice", validate_voice_length(voice_full)

        if voice_full or text:
            self._push_history(Message("assistant", buffer))

        yield "text", text

    # ------------------------------------------------------------------
    # 툴 루프 경로 (non-streaming)
    # ------------------------------------------------------------------

    async def _tool_voice_first(self, provider, messages: list[Message], original_transcript: str):
        tools = self._all_schemas()
        filler_sent = False

        for iteration in range(self._max_iterations):
            resp = await provider.complete(messages, tools)

            if resp.stop_reason == "tool_use":
                # filler는 첫 툴 호출 시 1회만
                if not filler_sent:
                    yield "filler", "searching"
                    filler_sent = True

                # 어시스턴트 메시지 (tool_use 블록 포함) 누적
                asst_blocks = [b.model_dump() for b in resp.content]
                messages.append(Message("assistant", asst_blocks))

                # 툴 호출
                tool_results = []
                for block in resp.content:
                    if block.type == "tool_use":
                        log.info("Tool call: %s(%s)", block.name, block.input)
                        result = await self._call_tool_safe(block.name, block.input)
                        log.info("Tool result: %s", result[:200])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                messages.append(Message("user", tool_results))

            else:
                # 최종 텍스트 응답
                raw = "".join(b.text for b in resp.content if b.type == "text")
                voice, text = parse_dual_response(raw)
                voice = validate_voice_length(voice)

                self._push_history(Message("user", original_transcript))
                self._push_history(Message("assistant", raw))

                yield "voice", voice
                yield "text", text
                return

        # max_iterations 초과
        log.error("Tool loop exceeded max_iterations=%d", self._max_iterations)
        yield "voice", "처리 중 문제가 생겼어요."
        yield "text", f"[Error] tool_use loop exceeded {self._max_iterations} iterations"

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
