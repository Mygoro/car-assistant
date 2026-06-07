"""Phase 6: LLM 텍스트 응답 오케스트레이터 + MCP/native 툴 통합.

인텐트 분류 → 프로바이더 선택 → (툴 루프) → 스트리밍 응답 → JSON 파싱 → 히스토리.
"""
import asyncio
import json
import logging
import os
import re
import time
from collections import deque
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Awaitable, Optional

from .providers.base import Message, Delta
from .providers.anthropic import AnthropicProvider
from .providers.ollama import OllamaProvider

log = logging.getLogger(__name__)

_RESET_KEYWORDS = {"새로 시작해", "새로시작해", "리셋", "초기화", "대화 초기화"}

# voice_response 값이 완성된 시점을 스트림 중에 감지
_VOICE_RE = re.compile(r'"voice_response"\s*:\s*"((?:[^"\\]|\\.)*)"')

# voice_response 값의 *시작* 위치(여는 따옴표 직후)를 찾는 패턴 — 부분 스트리밍용
_VOICE_START_RE = re.compile(r'"voice_response"\s*:\s*"')


def _find_value_end(raw: str) -> int:
    """JSON 문자열 본문 raw에서 이스케이프되지 않은 닫는 따옴표 인덱스. 없으면 -1."""
    i, n = 0, len(raw)
    while i < n:
        c = raw[i]
        if c == "\\":
            i += 2          # 이스케이프 시퀀스 건너뜀(끝의 외톨이 \는 자연히 -1)
            continue
        if c == '"':
            return i
        i += 1
    return -1


def _decode_partial(raw_value: str) -> str:
    """JSON 문자열 본문(따옴표 제외, 끝이 미완성 이스케이프일 수 있음)을 디코딩.

    끝에서부터 잘라가며 파싱 가능한 최대 prefix를 구한다(미완 \\u12 / 외톨이 \\ 처리).
    """
    s = raw_value
    while s:
        try:
            return json.loads('"' + s + '"')
        except json.JSONDecodeError:
            s = s[:-1]
    return ""


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

def build_system_prompt(memory_mode: str = "personal") -> str:
    template_path = Path("core/system_prompt_template.txt")
    memory_path = (
        Path("core/memory_exhibition.md")
        if memory_mode == "exhibition"
        else Path("core/memory.md")
    )

    template = template_path.read_text(encoding="utf-8")
    memory = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""

    now_kst = datetime.now(timezone(timedelta(hours=9)))
    weekdays_ko = ["월", "화", "수", "목", "금", "토", "일"]
    date_str = now_kst.strftime(f"%Y-%m-%d ({weekdays_ko[now_kst.weekday()]}요일)")

    return (
        template
        .replace("{MEMORY_MD_INJECTION_POINT}", memory)
        .replace("{CURRENT_DATETIME}", date_str)
    )


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

# JSON 파싱 실패 + voice 구제까지 실패했을 때 읽어줄 안전 멘트.
# 절대 raw JSON을 TTS로 흘려보내지 않기 위함(필드명·구조가 그대로 낭독되는 사고 방지).
_SAFE_VOICE_FALLBACK = "응답을 처리하다 문제가 생겼어요. 다시 한 번 말씀해 주실래요?"

# voice_response 하드 상한. 프롬프트 목표는 1~2문장(50~100자)이며,
# 약간의 초과는 허용하되 폭주(수백 자 → 수십 초 낭독)는 여기서 차단한다.
_VOICE_MAX_CHARS = 130


def parse_dual_response(raw: str) -> tuple[str, str]:
    try:
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.DOTALL)
        obj = json.loads(cleaned)
        voice = obj.get("voice_response", "")
        text = obj.get("text_response", "")
        return voice, text
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        log.warning("JSON parse failed: %s. Raw: %s", e, raw[:200])
        # 구제 1: voice_response 값만 추출(JSON이 깨졌거나 max_tokens로 잘렸어도
        # _decode_partial이 파싱 가능한 최대 prefix를 복구). raw JSON은 절대 읽지 않는다.
        m = _VOICE_START_RE.search(raw)
        if m:
            tail = raw[m.end():]
            end = _find_value_end(tail)
            value_raw = tail if end < 0 else tail[:end]
            voice = _decode_partial(value_raw)
            if voice:
                return voice, raw
        # 구제 2: voice도 못 건지면 안전 멘트만 읽고, 깨진 원문은 채팅(text)으로만.
        return _SAFE_VOICE_FALLBACK, raw


def validate_voice_length(voice: str) -> str:
    if len(voice) <= _VOICE_MAX_CHARS:
        return voice
    log.warning("voice_response %d자 초과 — 잘라냄: %s...", len(voice), voice[:60])
    head = voice[:_VOICE_MAX_CHARS]
    # 상한 이내의 마지막 문장 종결부호에서 자른다.
    cut = max(head.rfind("."), head.rfind("!"), head.rfind("?"), head.rfind("。"))
    if cut >= 40:                       # 너무 앞에서 잘려 내용이 사라지는 것 방지
        return head[:cut + 1].rstrip()
    return head.rstrip() + "…"          # 종결부호가 없으면 하드 컷 + 말줄임


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
        self._max_result_chars = tool_cfg.get("max_result_chars", 6000)

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
                # B) allowed_tools가 있으면 그 목록만 등록(ITPM/토큰 절감). 없으면 전체.
                allowed = set(scfg.get("allowed_tools") or [])
                registered = 0
                for tool in tools_result.tools:
                    if allowed and tool.name not in allowed:
                        continue
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
                    registered += 1
                log.info("MCP '%s' 연결 완료, 툴 %d/%d개 등록%s",
                         server_name, registered, len(tools_result.tools),
                         " (화이트리스트)" if allowed else "")
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
        from .native_tools.calendar import (
            get_calendar_events,
            create_calendar_event,
            update_calendar_event,
            delete_calendar_event,
        )
        from .native_tools.vehicle import get_vehicle_status
        from .native_tools.kakao import search_nearby_places, reverse_geocode, get_directions
        from .native_tools.web_search import web_search
        from .native_tools.google_places import get_place_details

        self._register_native(
            name="get_calendar_events",
            description="Google Calendar 일정 조회. 결과 각 줄 앞의 [id]는 수정·삭제 시 event_id로 사용.",
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
            name="create_calendar_event",
            description="Google Calendar 일정 생성.",
            input_schema={
                "type": "object",
                "properties": {
                    "summary":     {"type": "string", "description": "일정 제목"},
                    "start":       {"type": "string", "description": "시작 시각 ISO datetime, e.g. 2026-06-10T15:00:00"},
                    "end":         {"type": "string", "description": "종료 시각 ISO datetime (생략 시 start + 1시간)"},
                    "location":    {"type": "string", "description": "장소 (선택)"},
                    "description": {"type": "string", "description": "메모 (선택)"},
                },
                "required": ["summary", "start"],
            },
            fn=create_calendar_event,
        )
        self._register_native(
            name="update_calendar_event",
            description="Google Calendar 일정 수정. event_id는 get_calendar_events 결과의 [id].",
            input_schema={
                "type": "object",
                "properties": {
                    "event_id":    {"type": "string", "description": "수정할 이벤트 ID"},
                    "summary":     {"type": "string", "description": "새 제목 (선택)"},
                    "start":       {"type": "string", "description": "새 시작 시각 ISO datetime (선택)"},
                    "end":         {"type": "string", "description": "새 종료 시각 ISO datetime (선택)"},
                    "location":    {"type": "string", "description": "새 장소 (선택)"},
                    "description": {"type": "string", "description": "새 메모 (선택)"},
                },
                "required": ["event_id"],
            },
            fn=update_calendar_event,
        )
        self._register_native(
            name="delete_calendar_event",
            description="Google Calendar 일정 삭제. event_id는 get_calendar_events 결과의 [id].",
            input_schema={
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "삭제할 이벤트 ID"},
                },
                "required": ["event_id"],
            },
            fn=delete_calendar_event,
        )
        self._register_native(
            name="get_vehicle_status",
            description="차량의 주행 가능 거리(DTE)와 누적 주행거리를 조회.",
            input_schema={"type": "object", "properties": {}},
            fn=get_vehicle_status,
        )
        self._register_native(
            name="search_nearby_places",
            description=(
                "장소 검색. 주유소, 충전소, 맛집 등. 좌표(lon/lat)는 선택 — "
                "좌표를 모르면 지역명을 query에 넣어 검색(예: query='강남역 주유소')."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색어. 좌표가 없으면 지역명 포함, e.g. '강남역 주유소'"},
                    "lon": {"type": "number", "description": "경도 (선택)"},
                    "lat": {"type": "number", "description": "위도 (선택)"},
                    "radius_m": {"type": "integer", "description": "검색 반경 미터 (기본 5000, 좌표 있을 때만)"},
                },
                "required": ["query"],
            },
            fn=search_nearby_places,
        )
        self._register_native(
            name="get_directions",
            description=(
                "자동차 길찾기. 출발지→목적지 소요시간/거리/통행료 조회. "
                "지명만 주면 됨(GPS 불필요), e.g. origin='강남역', destination='잠실역'. "
                "departure_time을 주면 그 미래 시각 교통량 기준으로 예측."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "origin": {"type": "string", "description": "출발지 지명/주소. 예: 강남역, 판교 카카오"},
                    "destination": {"type": "string", "description": "목적지 지명/주소"},
                    "priority": {"type": "string", "description": "RECOMMEND(기본)/TIME(최단시간)/DISTANCE(최단거리)"},
                    "departure_time": {"type": "string", "description": "미래 출발 시각 ISO datetime, e.g. 2026-06-07T09:00:00. 현재 이후만 유효. 생략 시 현재 기준"},
                },
                "required": ["origin", "destination"],
            },
            fn=get_directions,
        )
        self._register_native(
            name="web_search",
            description=(
                "웹 검색(Brave). 영업시간·가격·메뉴·가게 특징·최신 정보 등 "
                "카카오 장소검색이 못 주는 정보를 찾을 때. "
                "장소 위치/거리/길찾기는 search_nearby_places·get_directions 우선."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색어. 예: '잠실 핫이즈타코 영업시간'"},
                    "count": {"type": "integer", "description": "결과 수 (기본 5, 최대 10)"},
                },
                "required": ["query"],
            },
            fn=web_search,
        )
        self._register_native(
            name="get_place_details",
            description=(
                "장소의 영업시간·평점·리뷰·가격대·전화번호 조회(Google Places). "
                "'지금 영업해?', '평점 어때?', '비싼 곳이야?', '리뷰 좋아?' 류에 사용. "
                "단순 위치/거리/길찾기는 search_nearby_places·get_directions 우선."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "장소명(지역 포함 권장). 예: '잠실 핫이즈타코', '강남대로 스타벅스'"},
                },
                "required": ["query"],
            },
            fn=get_place_details,
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
            log.warning("[TOOL] ✗ '%s' 미등록", name)
            return f"[Tool error: '{name}' 미등록]"
        args_str = json.dumps(arguments, ensure_ascii=False)
        log.info("[TOOL] ▶ %s %s", name, args_str[:300])
        t0 = time.monotonic()
        try:
            if handle.kind == "mcp":
                result = await asyncio.wait_for(
                    self._sessions[handle.mcp_server].call_tool(name, arguments),
                    timeout=self._tool_timeout_s,
                )
                texts = [c.text for c in result.content if hasattr(c, "text")]
                out = "\n".join(texts) if texts else "[Tool returned no text]"
            else:
                out = await asyncio.wait_for(
                    handle.native_fn(arguments),
                    timeout=self._tool_timeout_s,
                )
            out = self._truncate_result(name, out)
            log.info("[TOOL] ■ %s (%.2fs) → %s", name, time.monotonic() - t0, out[:300])
            return out
        except asyncio.TimeoutError:
            log.warning("[TOOL] ✗ %s timeout (%.2fs)", name, time.monotonic() - t0)
            return f"[Tool '{name}' timed out after {self._tool_timeout_s}s]"
        except Exception as e:
            log.error("[TOOL] ✗ %s error (%.2fs): %s", name, time.monotonic() - t0, e)
            return f"[Tool '{name}' error: {e}]"

    def _truncate_result(self, name: str, out) -> str:
        """C) 거대 tool_result를 캡. 매 루프 iteration·히스토리에 uncached로 재전송되며
        ITPM을 터뜨리는 것을 막는다. 모델은 앞부분만으로 요약 가능."""
        s = "" if out is None else str(out)
        if len(s) <= self._max_result_chars:
            return s
        log.info("[TOOL] '%s' 결과 %d자 → %d자로 잘림", name, len(s), self._max_result_chars)
        return s[:self._max_result_chars] + (
            f"\n…[결과 잘림: 전체 {len(s)}자 중 앞 {self._max_result_chars}자만 전달]"
        )

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

    async def run_voice_streaming(self, transcript: str):
        """⑥ Overlap 파이프라인 — voice_response를 토큰 단위로 흘려보낸다.

        run_voice_first가 voice_response *완성* 후 한 번에 방출하는 것과 달리,
        이 메서드는 생성되는 즉시 부분 텍스트를 yield해 WS TTS와 LLM을 겹친다.

        Yields:
            ('voice_chunk', str) — voice_response의 새로 디코딩된 조각 (0회 이상)
            ('voice_end',   '')  — voice_response 문자열 종료(WS EOS 신호)
            ('text',        str) — 전체 응답 완성 후 text_response (Discord 게시)
        """
        if any(kw in transcript for kw in _RESET_KEYWORDS):
            self._history.clear()
            log.info("Conversation history reset")
            yield "voice_chunk", "대화 기록을 초기화했어요."
            yield "voice_end", ""
            yield "text", "(히스토리 초기화)"
            return

        intent = classify_intent(transcript)
        provider = self._get_provider(intent)
        log.info("Intent: %s | model: %s", intent, provider.model)
        messages = self._build_messages(transcript)

        buffer = ""
        voice_start = -1       # voice 값 시작 인덱스(여는 따옴표 직후)
        emitted = 0            # 이미 yield한 디코딩 문자 수
        voice_ended = False

        async for delta in provider.stream(messages, tools=[]):
            if not delta.text:
                continue
            buffer += delta.text

            if voice_start < 0:
                m = _VOICE_START_RE.search(buffer)
                if not m:
                    continue
                voice_start = m.end()

            if voice_ended:
                continue

            raw = buffer[voice_start:]
            end = _find_value_end(raw)
            value_raw = raw if end < 0 else raw[:end]
            decoded = _decode_partial(value_raw)
            if len(decoded) > emitted:
                yield "voice_chunk", decoded[emitted:]
                emitted = len(decoded)
            if end >= 0:
                voice_ended = True
                yield "voice_end", ""

        # 스트림 종료 — voice를 한 번도 못 닫았으면(파싱 실패/포맷 이탈) 폴백
        voice_full, text = parse_dual_response(buffer)
        if not voice_ended:
            if emitted == 0 and voice_full:
                yield "voice_chunk", validate_voice_length(voice_full)
            yield "voice_end", ""

        if voice_full or text:
            self._push_history(Message("user", transcript))
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
            log.info("[TOOL] iteration %d/%d stop_reason=%s", iteration + 1, self._max_iterations, resp.stop_reason)

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
                        result = await self._call_tool_safe(block.name, block.input)
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
        memory_mode = self._cfg.get("memory_mode", "personal")
        msgs: list[Message] = [Message("system", build_system_prompt(memory_mode))]
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
